import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/config/app_config.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../../../core/utils/validators.dart';
import '../../data/auth_repository.dart';

class PhoneVerificationScreen extends ConsumerStatefulWidget {
  final String companyName;
  final String inviteToken;

  const PhoneVerificationScreen({
    super.key,
    required this.companyName,
    required this.inviteToken,
  });

  @override
  ConsumerState<PhoneVerificationScreen> createState() => _PhoneVerificationScreenState();
}

class _PhoneVerificationScreenState extends ConsumerState<PhoneVerificationScreen> {
  final _phoneController = TextEditingController();
  final _otpController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  bool _otpSent = false;
  bool _isLoading = false;

  void _sendOtp() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    try {
      final repo = ref.read(authRepositoryProvider);
      final response = await repo.sendOtp(_phoneController.text.trim());

      setState(() {
        _isLoading = false;
        _otpSent = true;
      });

      if (mounted) {
        final demoOtp = response['demo_otp'] ?? '123456';
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('OTP sent! Use code: $demoOtp')),
        );
      }
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to send OTP: $e'), backgroundColor: Theme.of(context).colorScheme.error),
        );
      }
    }
  }

  void _verifyOtp() async {
    if (_otpController.text.trim().length != 6) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Invalid OTP length.')),
      );
      return;
    }

    setState(() => _isLoading = true);
    
    try {
      final repo = ref.read(authRepositoryProvider);
      final response = await repo.verifyOtp(
        _phoneController.text.trim(), 
        _otpController.text.trim(), 
        widget.inviteToken,
      );

      // Save credentials to SecureStorage
      await SecureStorage.setPhoneNumber(_phoneController.text.trim());
      await SecureStorage.setAccessToken(response['access_token']);
      if (response['driver_id'] != null) {
        await SecureStorage.setDriverId(response['driver_id']);
      }
      if (response['verification_status'] != null) {
        await SecureStorage.setVerificationStatus(response['verification_status']);
      }

      setState(() => _isLoading = false);

      if (mounted) {
        if (response['is_new_driver'] == true || response['verification_status'] != 'APPROVED') {
          context.go('/auth/profile');
        } else {
          context.go('/home'); // Send straight to home if already approved
        }
      }
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Invalid OTP or verify failed'), backgroundColor: Theme.of(context).colorScheme.error),
        );
      }
    }
  }

  @override
  void dispose() {
    _phoneController.dispose();
    _otpController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Phone Verification')),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                _otpSent ? 'Enter Verification Code' : 'Verify Mobile Number',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
              ),
              const SizedBox(height: 8),
              Text(
                _otpSent
                    ? 'Enter 6-digit OTP sent to ${_phoneController.text}'
                    : 'Joining fleet: ${widget.companyName.isNotEmpty ? widget.companyName : "FleetGuard Partner"}',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Theme.of(context).colorScheme.outline,
                    ),
              ),
              const SizedBox(height: 32),
              if (!_otpSent) ...[
                TextFormField(
                  controller: _phoneController,
                  keyboardType: TextInputType.phone,
                  decoration: const InputDecoration(
                    labelText: 'Mobile Number',
                    hintText: '9876543210',
                    prefixText: '+91 ',
                    prefixIcon: Icon(Icons.phone),
                  ),
                  validator: Validators.phoneNumber,
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _sendOtp,
                    child: _isLoading
                        ? const CircularProgressIndicator()
                        : const Text('Send OTP'),
                  ),
                ),
              ] else ...[
                TextFormField(
                  controller: _otpController,
                  keyboardType: TextInputType.number,
                  maxLength: 6,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 24, letterSpacing: 8, fontWeight: FontWeight.bold),
                  decoration: const InputDecoration(
                    labelText: '6-Digit OTP',
                    hintText: '123456',
                  ),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _verifyOtp,
                    child: _isLoading
                        ? const CircularProgressIndicator()
                        : const Text('Verify & Continue'),
                  ),
                ),
                Center(
                  child: TextButton(
                    onPressed: () => setState(() => _otpSent = false),
                    child: const Text('Change Phone Number'),
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
