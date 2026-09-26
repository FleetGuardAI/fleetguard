/// Simple data classes for offline queue storage.
/// Uses sqflite instead of isar for Dart 3.13 compatibility.

class OfflinePOD {
  final int? id;
  final String tripId;
  final String base64Image;
  final String notes;
  final bool isSynced;
  final DateTime createdAt;

  OfflinePOD({
    this.id,
    required this.tripId,
    required this.base64Image,
    required this.notes,
    required this.isSynced,
    required this.createdAt,
  });

  Map<String, dynamic> toMap() => {
        if (id != null) 'id': id,
        'tripId': tripId,
        'base64Image': base64Image,
        'notes': notes,
        'isSynced': isSynced ? 1 : 0,
        'createdAt': createdAt.toIso8601String(),
      };

  factory OfflinePOD.fromMap(Map<String, dynamic> map) => OfflinePOD(
        id: map['id'] as int?,
        tripId: map['tripId'] as String,
        base64Image: map['base64Image'] as String,
        notes: map['notes'] as String,
        isSynced: (map['isSynced'] as int) == 1,
        createdAt: DateTime.parse(map['createdAt'] as String),
      );
}

class OfflineExpense {
  final int? id;
  final double amount;
  final String category;
  final String description;
  final String base64ReceiptImage;
  final bool isSynced;
  final DateTime createdAt;

  OfflineExpense({
    this.id,
    required this.amount,
    required this.category,
    required this.description,
    required this.base64ReceiptImage,
    required this.isSynced,
    required this.createdAt,
  });

  Map<String, dynamic> toMap() => {
        if (id != null) 'id': id,
        'amount': amount,
        'category': category,
        'description': description,
        'base64ReceiptImage': base64ReceiptImage,
        'isSynced': isSynced ? 1 : 0,
        'createdAt': createdAt.toIso8601String(),
      };

  factory OfflineExpense.fromMap(Map<String, dynamic> map) => OfflineExpense(
        id: map['id'] as int?,
        amount: (map['amount'] as num).toDouble(),
        category: map['category'] as String,
        description: map['description'] as String,
        base64ReceiptImage: map['base64ReceiptImage'] as String,
        isSynced: (map['isSynced'] as int) == 1,
        createdAt: DateTime.parse(map['createdAt'] as String),
      );
}

class OfflineLocation {
  final int? id;
  final double latitude;
  final double longitude;
  final double speed;
  final double heading;
  final bool isSynced;
  final DateTime timestamp;

  OfflineLocation({
    this.id,
    required this.latitude,
    required this.longitude,
    required this.speed,
    required this.heading,
    required this.isSynced,
    required this.timestamp,
  });

  Map<String, dynamic> toMap() => {
        if (id != null) 'id': id,
        'latitude': latitude,
        'longitude': longitude,
        'speed': speed,
        'heading': heading,
        'isSynced': isSynced ? 1 : 0,
        'timestamp': timestamp.toIso8601String(),
      };

  factory OfflineLocation.fromMap(Map<String, dynamic> map) => OfflineLocation(
        id: map['id'] as int?,
        latitude: (map['latitude'] as num).toDouble(),
        longitude: (map['longitude'] as num).toDouble(),
        speed: (map['speed'] as num).toDouble(),
        heading: (map['heading'] as num).toDouble(),
        isSynced: (map['isSynced'] as int) == 1,
        timestamp: DateTime.parse(map['timestamp'] as String),
      );
}
