import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/config/app_config.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../../../core/utils/validators.dart';

class PhoneVerificationScreen extends StatefulWidget {
  final String companyName;
  final String inviteToken;

  const PhoneVerificationScreen({
    super.key,
    required this.companyName,
    required this.inviteToken,
  });

  @override
  State<PhoneVerificationScreen> createState() => _PhoneVerificationScreenState();
}

class _PhoneVerificationScreenState extends State<PhoneVerificationScreen> {
  final _phoneController = TextEditingController();
  final _otpController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  bool _otpSent = false;
  bool _isLoading = false;

  void _sendOtp() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    await Future.delayed(const Duration(seconds: 1)); // Simulate API

    setState(() {
      _isLoading = false;
      _otpSent = true;
    });

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('OTP sent! Use demo code: ${AppConfig.demoOtpCode}')),
      );
    }
  }

  void _verifyOtp() async {
    if (_otpController.text.trim() != AppConfig.demoOtpCode && _otpController.text.length != 6) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Invalid OTP. Use demo OTP: 123456')),
      );
      return;
    }

    setState(() => _isLoading = true);
    await Future.delayed(const Duration(seconds: 1));

    // Save demo credentials to SecureStorage
    await SecureStorage.setPhoneNumber(_phoneController.text.trim());
    await SecureStorage.setAccessToken("demo_jwt_access_token_driver_2026");
    await SecureStorage.setDriverId(1);
    await SecureStorage.setVerificationStatus("PENDING_DOCUMENTS");

    setState(() => _isLoading = false);

    if (mounted) {
      context.go('/auth/profile');
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
