import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/storage/secure_storage.dart';
import '../../../../core/config/theme/app_colors.dart';
import '../../data/auth_repository.dart';

class PendingApprovalScreen extends ConsumerStatefulWidget {
  const PendingApprovalScreen({super.key});

  @override
  ConsumerState<PendingApprovalScreen> createState() => _PendingApprovalScreenState();
}

class _PendingApprovalScreenState extends ConsumerState<PendingApprovalScreen> {
  String _companyName = '';
  bool _isChecking = false;

  @override
  void initState() {
    super.initState();
    _loadCompanyName();
  }

  Future<void> _loadCompanyName() async {
    final name = await SecureStorage.getCompanyName();
    if (name != null && mounted) {
      setState(() => _companyName = name);
    }
  }

  Future<void> _checkStatus() async {
    setState(() => _isChecking = true);
    try {
      final repo = ref.read(authRepositoryProvider);
      final profile = await repo.getProfile();
      final status = profile['verification_status'];
      
      await SecureStorage.setVerificationStatus(status ?? '');

      if (status == 'APPROVED') {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Approved! Redirecting to dashboard...'), backgroundColor: AppColors.success),
          );
          context.go('/dashboard');
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Status: ${(status ?? 'PENDING').replaceAll('_', ' ')}. Please wait for fleet admin approval.'),
              backgroundColor: Colors.orange,
            ),
          );
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error checking status: $e'), backgroundColor: AppColors.error),
        );
      }
    } finally {
      if (mounted) setState(() => _isChecking = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(32.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: Colors.orange.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.hourglass_top_rounded,
                size: 80,
                color: Colors.orange,
              ),
            ),
            const SizedBox(height: 32),
            Text(
              'Pending Fleet Approval',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            if (_companyName.isNotEmpty) ...[
              const SizedBox(height: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.mutedGreen,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  _companyName,
                  style: const TextStyle(
                    color: AppColors.primaryDark,
                    fontWeight: FontWeight.w600,
                    fontSize: 14,
                  ),
                ),
              ),
            ],
            const SizedBox(height: 12),
            const Text(
              'Your profile and documents have been submitted successfully. A fleet administrator will review and approve your account shortly.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 48),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isChecking ? null : _checkStatus,
                icon: _isChecking
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.refresh),
                label: Text(_isChecking ? 'Checking...' : 'Refresh Status'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
