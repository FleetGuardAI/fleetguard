import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/theme/app_colors.dart';
import '../../../../core/router/app_router.dart';
import 'package:google_fonts/google_fonts.dart';

class SplashScreen extends ConsumerWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final routerNotifier = ref.watch(routerNotifierProvider);
    final hasError = routerNotifier.hasError;

    return Scaffold(
      backgroundColor: AppColors.darkBackground,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // FleetGuard Logo / Branding
            Icon(
              Icons.directions_car_rounded,
              size: 80,
              color: AppColors.primary,
            ),
            const SizedBox(height: 24),
            Text(
              'FleetGuard',
              style: GoogleFonts.inter(
                fontSize: 32,
                fontWeight: FontWeight.w700,
                color: Colors.white,
                letterSpacing: -1,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'OWNER',
              style: GoogleFonts.inter(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: AppColors.primary,
                letterSpacing: 4,
              ),
            ),
            const SizedBox(height: 60),

            if (!hasError) ...[
              const CircularProgressIndicator(
                color: AppColors.primary,
              ),
              const SizedBox(height: 24),
              Text(
                'Connecting to FleetGuard...',
                style: GoogleFonts.inter(
                  color: AppColors.darkOnSurfaceVariant,
                  fontSize: 14,
                ),
              ),
            ] else ...[
              const Icon(
                Icons.error_outline,
                color: AppColors.error,
                size: 40,
              ),
              const SizedBox(height: 16),
              Text(
                'Unable to connect to FleetGuard',
                style: GoogleFonts.inter(
                  color: Colors.white,
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 32),
              ElevatedButton(
                onPressed: () => routerNotifier.retryInit(),
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 12),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                child: const Text('Retry'),
              ),
              const SizedBox(height: 16),
              TextButton(
                onPressed: () => routerNotifier.forceLogin(),
                style: TextButton.styleFrom(
                  foregroundColor: AppColors.darkOnSurfaceVariant,
                ),
                child: const Text('Continue to Login'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
