import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../auth/data/auth_repository.dart';

final documentsProvider = FutureProvider.autoDispose<List<dynamic>>((ref) async {
  final repo = ref.watch(authRepositoryProvider);
  return repo.getDocuments();
});
