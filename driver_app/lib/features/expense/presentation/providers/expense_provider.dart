import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/expense_repository.dart';

final driverExpensesProvider = FutureProvider.autoDispose<List<Map<String, dynamic>>>((ref) async {
  final repo = ref.watch(expenseRepositoryProvider);
  return repo.listDriverExpenses();
});
