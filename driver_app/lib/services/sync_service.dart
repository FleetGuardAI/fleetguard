import 'package:isar/isar.dart';
import 'package:workmanager/workmanager.dart';
import 'package:path_provider/path_provider.dart';
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
  final Isar isar;
  final Dio dio;

  SyncService(this.isar) : dio = Dio();

  static Future<SyncService> init() async {
    final dir = await getApplicationDocumentsDirectory();
    final isar = await Isar.open(
      [OfflinePODSchema, OfflineExpenseSchema, OfflineLocationSchema],
      directory: dir.path,
    );
    return SyncService(isar);
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

  Future<void> syncPendingRecords() async {
    await _syncLocations();
    await _syncPODs();
    await _syncExpenses();
  }

  Future<void> _syncLocations() async {
    final pendingLocations = await isar.offlineLocations.filter().isSyncedEqualTo(false).findAll();
    if (pendingLocations.isEmpty) return;

    // In a real app, you would send this to your backend via Dio
    // For now, we simulate a successful API call and mark them as synced
    await isar.writeTxn(() async {
      for (final loc in pendingLocations) {
        loc.isSynced = true;
        await isar.offlineLocations.put(loc);
      }
    });
  }

  Future<void> _syncPODs() async {
    final pendingPODs = await isar.offlinePODs.filter().isSyncedEqualTo(false).findAll();
    if (pendingPODs.isEmpty) return;

    await isar.writeTxn(() async {
      for (final pod in pendingPODs) {
        pod.isSynced = true;
        await isar.offlinePODs.put(pod);
      }
    });
  }

  Future<void> _syncExpenses() async {
    final pendingExpenses = await isar.offlineExpenses.filter().isSyncedEqualTo(false).findAll();
    if (pendingExpenses.isEmpty) return;

    await isar.writeTxn(() async {
      for (final expense in pendingExpenses) {
        expense.isSynced = true;
        await isar.offlineExpenses.put(expense);
      }
    });
  }
}
