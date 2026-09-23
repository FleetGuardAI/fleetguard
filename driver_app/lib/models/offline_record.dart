import 'package:isar/isar.dart';

part 'offline_record.g.dart';

@collection
class OfflinePOD {
  Id id = Isar.autoIncrement;

  @Index()
  late String tripId;

  late String base64Image;
  
  late String notes;

  @Index()
  late bool isSynced;
  
  late DateTime createdAt;
}

@collection
class OfflineExpense {
  Id id = Isar.autoIncrement;

  late double amount;
  
  late String category;
  
  late String description;
  
  late String base64ReceiptImage;

  @Index()
  late bool isSynced;
  
  late DateTime createdAt;
}

@collection
class OfflineLocation {
  Id id = Isar.autoIncrement;

  late double latitude;
  
  late double longitude;
  
  late double speed;
  
  late double heading;

  @Index()
  late bool isSynced;
  
  late DateTime timestamp;
}
