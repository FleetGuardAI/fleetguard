import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/config/theme/app_colors.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../data/auth_repository.dart';

class FleetMismatchScreen extends ConsumerStatefulWidget {
  const FleetMismatchScreen({
    super.key,
    required this.currentCompanyName,
    required this.targetCompanyName,
    required this.targetCompanyId,
    required this.inviteToken,
  });

  final String currentCompanyName;
  final String targetCompanyName;
  final int targetCompanyId;
  final String inviteToken;

  @override
  ConsumerState<FleetMismatchScreen> createState() => _FleetMismatchScreenState();
}

class _FleetMismatchScreenState extends ConsumerState<FleetMismatchScreen> {
  bool _isSubmitting = false;

  Future<void> _handleContinue() async {
    setState(() => _isSubmitting = true);

    try {
      final repo = ref.read(authRepositoryProvider);
      final response = await repo.requestFleetTransfer(
        widget.inviteToken,
        widget.targetCompanyId,
      );

      // Save pending target company info
      await SecureStorage.setVerificationStatus('PENDING_APPROVAL');

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            response['message'] ?? 'Fleet transfer request submitted successfully!',
          ),
          backgroundColor: AppColors.success,
        ),
      );

      // Navigate to pending approval status screen
      context.go('/auth/pending-approval');
    } catch (e) {
      if (!mounted) return;
      setState(() => _isSubmitting = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error initiating transfer: $e'),
          backgroundColor: AppColors.error,
        ),
      );
    }
  }

  Future<void> _handleCancel() async {
    final isLoggedIn = await SecureStorage.isLoggedIn();
    if (!mounted) return;
    if (isLoggedIn) {
      context.go('/dashboard');
    } else {
      context.go('/auth/login');
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: AppColors.lightBackground,
      appBar: AppBar(
        title: const Text('Fleet Transfer'),
        centerTitle: true,
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.close_rounded),
          onPressed: _handleCancel,
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Alert Header Icon
              Center(
                child: Container(
                  width: 72,
                  height: 72,
                  decoration: BoxDecoration(
                    color: AppColors.warning.withOpacity(0.12),
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: AppColors.warning.withOpacity(0.4),
                      width: 2,
                    ),
                  ),
                  child: const Icon(
                    Icons.swap_horiz_rounded,
                    size: 40,
                    color: AppColors.warning,
                  ),
                ),
              ),
              const SizedBox(height: 20),

              Center(
                child: Text(
                  'Switching Fleet Assignment',
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: AppColors.deepGraphite,
                  ),
                ),
              ),
              const SizedBox(height: 8),

              // Visual Transfer Comparison Card
              Container(
                margin: const EdgeInsets.only(top: 20, bottom: 24),
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: AppColors.lightBorder),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.04),
                      blurRadius: 16,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    // Current Fleet
                    _buildFleetRow(
                      context: context,
                      label: 'CURRENT FLEET',
                      fleetName: widget.currentCompanyName.isNotEmpty
                          ? widget.currentCompanyName
                          : 'Current Assigned Fleet',
                      icon: Icons.business_rounded,
                      color: AppColors.coolGray,
                      badge: 'Active Now',
                      badgeColor: AppColors.coolGray,
                    ),

                    // Divider with Arrow
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 16.0),
                      child: Row(
                        children: [
                          Expanded(
                            child: Container(
                              height: 1,
                              color: AppColors.lightBorder,
                            ),
                          ),
                          Container(
                            margin: const EdgeInsets.symmetric(horizontal: 12),
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              color: AppColors.mutedGreen,
                              shape: BoxShape.circle,
                              border: Border.all(
                                color: AppColors.primary.withOpacity(0.3),
                              ),
                            ),
                            child: const Icon(
                              Icons.arrow_downward_rounded,
                              size: 18,
                              color: AppColors.primary,
                            ),
                          ),
                          Expanded(
                            child: Container(
                              height: 1,
                              color: AppColors.lightBorder,
                            ),
                          ),
                        ],
                      ),
                    ),

                    // Target Fleet
                    _buildFleetRow(
                      context: context,
                      label: 'NEW FLEET (SCANNED)',
                      fleetName: widget.targetCompanyName.isNotEmpty
                          ? widget.targetCompanyName
                          : 'Target Fleet',
                      icon: Icons.local_shipping_rounded,
                      color: AppColors.primary,
                      badge: 'Target Fleet',
                      badgeColor: AppColors.primary,
                    ),
                  ],
                ),
              ),

              // Official Disclosure Callout
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFF9E6), // Light warm warning tint
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: const Color(0xFFFFE082)),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(
                      Icons.info_outline_rounded,
                      color: Color(0xFFE65100),
                      size: 22,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'You are switching to a new fleet. Your current fleet assignment will be replaced only after the new registration and approval process is completed.',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: const Color(0xFF5D4037),
                          height: 1.4,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 16),

              // Policy Details
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.lightBorder),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildBullet(
                      theme: theme,
                      icon: Icons.shield_outlined,
                      text: 'Your historical trips, expenses, and documents in your current fleet are safely preserved.',
                    ),
                    const SizedBox(height: 10),
                    _buildBullet(
                      theme: theme,
                      icon: Icons.file_copy_outlined,
                      text: 'Existing verified KYC documents will be reused to speed up your onboarding.',
                    ),
                    const SizedBox(height: 10),
                    _buildBullet(
                      theme: theme,
                      icon: Icons.approval_outlined,
                      text: 'You will remain active under your current fleet until the new fleet admin approves this request.',
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 32),

              // Continue Registration Button
              ElevatedButton(
                onPressed: _isSubmitting ? null : _handleContinue,
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleTransitions.circle(borderRadius: BorderRadius.circular(14)),
                  elevation: 2,
                ),
                child: _isSubmitting
                    ? const SizedBox(
                        height: 22,
                        width: 22,
                        child: CircularProgressIndicator(
                          strokeWidth: 2.5,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      )
                    : Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text(
                            'Continue Registration',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(width: 8),
                          const Icon(Icons.arrow_forward_rounded, size: 20),
                        ],
                      ),
              ),

              const SizedBox(height: 12),

              // Cancel Button
              OutlinedButton(
                onPressed: _isSubmitting ? null : _handleCancel,
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  side: BorderSide(color: AppColors.lightBorder, width: 1.5),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
                child: Text(
                  'Cancel & Stay in Current Fleet',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: AppColors.coolGray,
                  ),
                ),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildFleetRow({
    required BuildContext context,
    required String label,
    required String fleetName,
    required IconData icon,
    required Color color,
    required String badge,
    required Color badgeColor,
  }) {
    final theme = Theme.of(context);

    return Row(
      children: [
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            color: color.withOpacity(0.12),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Icon(icon, color: color, size: 24),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: theme.textTheme.labelSmall?.copyWith(
                  color: AppColors.coolGray,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 0.8,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                fleetName,
                style: theme.textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w700,
                  color: AppColors.deepGraphite,
                ),
              ),
            ],
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: badgeColor.withOpacity(0.12),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Text(
            badge,
            style: TextStyle(
              color: badgeColor,
              fontWeight: FontWeight.w700,
              fontSize: 11,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildBullet({
    required ThemeData theme,
    required IconData icon,
    required String text,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 18, color: AppColors.primary),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            text,
            style: theme.textTheme.bodySmall?.copyWith(
              color: AppColors.deepGraphite,
              height: 1.35,
            ),
          ),
        ),
      ],
    );
  }
}

class RoundedRectangleTransitions {
  static RoundedRectangleBorder circle({required BorderRadius borderRadius}) {
    return RoundedRectangleBorder(borderRadius: borderRadius);
  }
}
