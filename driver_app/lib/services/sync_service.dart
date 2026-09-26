import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'package:workmanager/workmanager.dart';
import 'package:fleetguard_driver/models/offline_record.dart';
import 'package:dio/dio.dart';

@pragma('vm:entry-point')
void callbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    try {
      final syncService = await SyncService.init();
      await syncService.syncPendingRecords();
      return Future.value(true);
    } catch (err) {
      return Future.value(false);
    }
  });
}

class SyncService {
  final Database db;
  final Dio dio;

  SyncService(this.db) : dio = Dio();

  static Future<SyncService> init() async {
    final dbPath = await getDatabasesPath();
    final db = await openDatabase(
      join(dbPath, 'fleetguard_offline.db'),
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE offline_pods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tripId TEXT NOT NULL,
            base64Image TEXT NOT NULL,
            notes TEXT NOT NULL,
            isSynced INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL
          )
        ''');
        await db.execute('''
          CREATE TABLE offline_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            base64ReceiptImage TEXT NOT NULL,
            isSynced INTEGER NOT NULL DEFAULT 0,
            createdAt TEXT NOT NULL
          )
        ''');
        await db.execute('''
          CREATE TABLE offline_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            speed REAL NOT NULL,
            heading REAL NOT NULL,
            isSynced INTEGER NOT NULL DEFAULT 0,
            timestamp TEXT NOT NULL
          )
        ''');
      },
    );
    return SyncService(db);
  }

  static void initializeWorkManager() {
    Workmanager().initialize(
      callbackDispatcher,
      isInDebugMode: true,
    );
    Workmanager().registerPeriodicTask(
      "1",
      "syncOfflineRecords",
      frequency: const Duration(minutes: 15),
      constraints: Constraints(
        networkType: NetworkType.connected,
      ),
    );
  }

  // --- PODs ---

  Future<void> savePod(OfflinePOD pod) async {
    await db.insert('offline_pods', pod.toMap());
  }

  Future<List<OfflinePOD>> getPendingPods() async {
    final rows = await db.query('offline_pods', where: 'isSynced = 0');
    return rows.map(OfflinePOD.fromMap).toList();
  }

  Future<void> markPodSynced(int id) async {
    await db.update('offline_pods', {'isSynced': 1}, where: 'id = ?', whereArgs: [id]);
  }

  // --- Expenses ---

  Future<void> saveExpense(OfflineExpense expense) async {
    await db.insert('offline_expenses', expense.toMap());
  }

  Future<List<OfflineExpense>> getPendingExpenses() async {
    final rows = await db.query('offline_expenses', where: 'isSynced = 0');
    return rows.map(OfflineExpense.fromMap).toList();
  }

  Future<void> markExpenseSynced(int id) async {
    await db.update('offline_expenses', {'isSynced': 1}, where: 'id = ?', whereArgs: [id]);
  }

  // --- Locations ---

  Future<void> saveLocation(OfflineLocation location) async {
    await db.insert('offline_locations', location.toMap());
  }

  Future<List<OfflineLocation>> getPendingLocations() async {
    final rows = await db.query('offline_locations', where: 'isSynced = 0');
    return rows.map(OfflineLocation.fromMap).toList();
  }

  Future<void> markLocationSynced(int id) async {
    await db.update('offline_locations', {'isSynced': 1}, where: 'id = ?', whereArgs: [id]);
  }

  // --- Sync ---

  Future<void> syncPendingRecords() async {
    await _syncLocations();
    await _syncPODs();
    await _syncExpenses();
  }

  Future<void> _syncLocations() async {
    final pendingLocations = await getPendingLocations();
    if (pendingLocations.isEmpty) return;
    for (final loc in pendingLocations) {
      loc.id != null ? await markLocationSynced(loc.id!) : null;
    }
  }

  Future<void> _syncPODs() async {
    final pendingPODs = await getPendingPods();
    if (pendingPODs.isEmpty) return;
    for (final pod in pendingPODs) {
      pod.id != null ? await markPodSynced(pod.id!) : null;
    }
  }

  Future<void> _syncExpenses() async {
    final pendingExpenses = await getPendingExpenses();
    if (pendingExpenses.isEmpty) return;
    for (final expense in pendingExpenses) {
      expense.id != null ? await markExpenseSynced(expense.id!) : null;
    }
  }
}
