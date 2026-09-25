import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/wallet_repository.dart';

final walletSummaryProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final repository = ref.watch(walletRepositoryProvider);
  return repository.getWalletSummary();
});
