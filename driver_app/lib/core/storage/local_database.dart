import 'dart:convert';
import 'package:path/path.dart';
import 'package:sqflite/sqflite.dart';

import '../utils/logger.dart';

/// Local SQLite database for offline data persistence.
/// Stores GPS locations, expenses, inspections, and sync queue items.
class LocalDatabase {
  static Database? _database;

  static Future<Database> get database async {
    _database ??= await _initDatabase();
    return _database!;
  }

  static Future<Database> _initDatabase() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'fleetguard_driver.db');

    AppLogger.info('Initializing local database at $path');

    return await openDatabase(
      path,
      version: 1,
      onCreate: _createTables,
      onUpgrade: _onUpgrade,
    );
  }

  static Future<void> _createTables(Database db, int version) async {
    // GPS location queue (offline buffering)
    await db.execute('''
      CREATE TABLE location_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        speed REAL,
        heading REAL,
        accuracy REAL,
        timestamp TEXT NOT NULL,
        battery_percent INTEGER,
        activity_state TEXT,
        synced INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
      )
    ''');

    // Offline sync queue (generic)
    await db.execute('''
      CREATE TABLE sync_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        action TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        payload TEXT NOT NULL,
        file_paths TEXT,
        retry_count INTEGER DEFAULT 0,
        max_retries INTEGER DEFAULT 5,
        status TEXT DEFAULT 'PENDING',
        error_message TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        last_attempt_at TEXT
      )
    ''');

    // Cached trips
    await db.execute('''
      CREATE TABLE cached_trips (
        id INTEGER PRIMARY KEY,
        data TEXT NOT NULL,
        updated_at TEXT DEFAULT (datetime('now'))
      )
    ''');

    // Cached vehicle info
    await db.execute('''
      CREATE TABLE cached_vehicle (
        id INTEGER PRIMARY KEY,
        data TEXT NOT NULL,
        updated_at TEXT DEFAULT (datetime('now'))
      )
    ''');

    // Cached documents (file paths)
    await db.execute('''
      CREATE TABLE cached_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_type TEXT NOT NULL,
        local_path TEXT NOT NULL,
        remote_url TEXT,
        updated_at TEXT DEFAULT (datetime('now'))
      )
    ''');

    // Driver profile cache
    await db.execute('''
      CREATE TABLE driver_profile_cache (
        id INTEGER PRIMARY KEY DEFAULT 1,
        data TEXT NOT NULL,
        updated_at TEXT DEFAULT (datetime('now'))
      )
    ''');

    // Notifications cache
    await db.execute('''
      CREATE TABLE notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        body TEXT NOT NULL,
        type TEXT NOT NULL,
        data TEXT,
        read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
      )
    ''');

    AppLogger.info('Local database tables created');
  }

  static Future<void> _onUpgrade(Database db, int oldVersion, int newVersion) async {
    // Handle future schema migrations here
    AppLogger.info('Database upgrade from v$oldVersion to v$newVersion');
  }

  // --- Location Queue Operations ---

  static Future<int> insertLocation(Map<String, dynamic> location) async {
    final db = await database;
    return await db.insert('location_queue', location);
  }

  static Future<List<Map<String, dynamic>>> getUnSyncedLocations({int limit = 50}) async {
    final db = await database;
    return await db.query(
      'location_queue',
      where: 'synced = 0',
      orderBy: 'id ASC',
      limit: limit,
    );
  }

  static Future<void> markLocationsSynced(List<int> ids) async {
    final db = await database;
    final batch = db.batch();
    for (final id in ids) {
      batch.update('location_queue', {'synced': 1}, where: 'id = ?', whereArgs: [id]);
    }
    await batch.commit(noResult: true);
  }

  static Future<void> cleanSyncedLocations() async {
    final db = await database;
    await db.delete('location_queue', where: 'synced = 1');
  }

  // --- Sync Queue Operations ---

  static Future<int> addToSyncQueue({
    required String entityType,
    required String action,
    required String endpoint,
    required Map<String, dynamic> payload,
    List<String>? filePaths,
  }) async {
    final db = await database;
    return await db.insert('sync_queue', {
      'entity_type': entityType,
      'action': action,
      'endpoint': endpoint,
      'payload': jsonEncode(payload),
      'file_paths': filePaths != null ? jsonEncode(filePaths) : null,
    });
  }

  static Future<List<Map<String, dynamic>>> getPendingSyncItems({int limit = 20}) async {
    final db = await database;
    return await db.query(
      'sync_queue',
      where: 'status = ? AND retry_count < max_retries',
      whereArgs: ['PENDING'],
      orderBy: 'created_at ASC',
      limit: limit,
    );
  }

  static Future<void> markSyncItemCompleted(int id) async {
    final db = await database;
    await db.update(
      'sync_queue',
      {'status': 'COMPLETED'},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  static Future<void> markSyncItemFailed(int id, String error) async {
    final db = await database;
    await db.rawUpdate('''
      UPDATE sync_queue 
      SET retry_count = retry_count + 1,
          error_message = ?,
          last_attempt_at = datetime('now'),
          status = CASE WHEN retry_count + 1 >= max_retries THEN 'FAILED' ELSE 'PENDING' END
      WHERE id = ?
    ''', [error, id]);
  }

  // --- Cache Operations ---

  static Future<void> cacheTrips(List<Map<String, dynamic>> trips) async {
    final db = await database;
    final batch = db.batch();
    batch.delete('cached_trips');
    for (final trip in trips) {
      batch.insert('cached_trips', {
        'id': trip['id'],
        'data': jsonEncode(trip),
      });
    }
    await batch.commit(noResult: true);
  }

  static Future<List<Map<String, dynamic>>> getCachedTrips() async {
    final db = await database;
    final rows = await db.query('cached_trips');
    return rows.map((r) => jsonDecode(r['data'] as String) as Map<String, dynamic>).toList();
  }

  static Future<void> cacheDriverProfile(Map<String, dynamic> profile) async {
    final db = await database;
    await db.insert(
      'driver_profile_cache',
      {'id': 1, 'data': jsonEncode(profile)},
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  static Future<Map<String, dynamic>?> getCachedDriverProfile() async {
    final db = await database;
    final rows = await db.query('driver_profile_cache', where: 'id = 1');
    if (rows.isEmpty) return null;
    return jsonDecode(rows.first['data'] as String) as Map<String, dynamic>;
  }

  // --- Notifications ---

  static Future<int> insertNotification({
    required String title,
    required String body,
    required String type,
    Map<String, dynamic>? data,
  }) async {
    final db = await database;
    return await db.insert('notifications', {
      'title': title,
      'body': body,
      'type': type,
      'data': data != null ? jsonEncode(data) : null,
    });
  }

  static Future<List<Map<String, dynamic>>> getNotifications({int limit = 50}) async {
    final db = await database;
    return await db.query(
      'notifications',
      orderBy: 'created_at DESC',
      limit: limit,
    );
  }

  static Future<int> getUnreadNotificationCount() async {
    final db = await database;
    final result = await db.rawQuery('SELECT COUNT(*) as count FROM notifications WHERE read = 0');
    return result.first['count'] as int;
  }

  static Future<void> markNotificationRead(int id) async {
    final db = await database;
    await db.update('notifications', {'read': 1}, where: 'id = ?', whereArgs: [id]);
  }

  // --- Reset ---
  static Future<void> clearAll() async {
    final db = await database;
    final batch = db.batch();
    batch.delete('location_queue');
    batch.delete('sync_queue');
    batch.delete('cached_trips');
    batch.delete('cached_vehicle');
    batch.delete('cached_documents');
    batch.delete('driver_profile_cache');
    batch.delete('notifications');
    await batch.commit(noResult: true);
    AppLogger.info('Local database cleared for logout');
  }
}
