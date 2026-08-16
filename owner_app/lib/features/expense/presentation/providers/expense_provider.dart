import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/expense_repository.dart';

final fleetExpensesProvider = StreamProvider.autoDispose<List<Map<String, dynamic>>>((ref) async* {
  final repo = ref.watch(fleetExpenseRepositoryProvider);
  
  // Yield initial value
  yield await repo.listFleetExpenses();
  
  // Poll every 10 seconds for live updates
  while (true) {
    await Future.delayed(const Duration(seconds: 10));
    try {
      yield await repo.listFleetExpenses();
    } catch (e) {
      continue;
    }
  }
});
