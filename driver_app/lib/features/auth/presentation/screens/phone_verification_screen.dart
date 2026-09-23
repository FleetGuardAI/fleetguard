import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'dart:convert';
import '../../../../core/config/app_config.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../../../core/utils/validators.dart';
import '../../data/auth_repository.dart';

class PhoneVerificationScreen extends ConsumerStatefulWidget {

  const PhoneVerificationScreen({
    super.key,
    this.companyName,
    this.inviteToken,
  });
  final String? companyName;
  final String? inviteToken;

  @override
  ConsumerState<PhoneVerificationScreen> createState() => _PhoneVerificationScreenState();
}

class _PhoneVerificationScreenState extends ConsumerState<PhoneVerificationScreen> {
  final _phoneController = TextEditingController();
  final _otpController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  bool _otpSent = false;
  bool _isLoading = false;
  String? _reqId;
  int _countdown = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
  }

  void _executeFleetGuardVerification() async {
    try {
      final repo = ref.read(authRepositoryProvider);
      final response = await repo.verifyOtp(
        _phoneController.text.trim(), 
        _reqId ?? 'widget-req',
        _otpController.text.trim(), 
        widget.inviteToken,
      );

      await SecureStorage.setPhoneNumber(_phoneController.text.trim());
      await SecureStorage.setAccessToken(response['access_token']);
      if (response['driver_id'] != null) {
        await SecureStorage.setDriverId(response['driver_id']);
      }
      if (response['verification_status'] != null) {
        await SecureStorage.setVerificationStatus(response['verification_status']);
      }
      // Store company name for welcome screen
      if (widget.companyName != null && widget.companyName!.isNotEmpty) {
        await SecureStorage.setCompanyName(widget.companyName!);
      }
      // Store invite token for session persistence
      if (widget.inviteToken != null && widget.inviteToken!.isNotEmpty) {
        await SecureStorage.setInviteToken(widget.inviteToken!);
      }

      setState(() => _isLoading = false);

      if (mounted) {
        if (response['is_new_driver'] == true || response['verification_status'] == 'PENDING_DOCUMENTS') {
          context.go('/auth/profile');
        } else if (response['verification_status'] == 'PENDING_APPROVAL') {
          context.go('/auth/pending-approval');
        } else {
          context.go('/dashboard');
        }
      }
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Verification failed: $e'), backgroundColor: Theme.of(context).colorScheme.error),
        );
      }
    }
  }

  void _startCountdown() {
    _countdown = 60;
    _timer?.cancel();
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_countdown > 0) {
        setState(() {
          _countdown--;
        });
      } else {
        timer.cancel();
      }
    });
  }

  void _sendOtp() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);
    debugPrint('[SERVER OTP] SEND_STARTED');
    
    String phone = _phoneController.text.trim();
    String formattedMobile = phone.replaceAll(RegExp(r'\D'), '');
    if (formattedMobile.length == 10) {
      formattedMobile = '91$formattedMobile';
    }
    
    try {
      final repo = ref.read(authRepositoryProvider);
      final response = await repo.sendOtp(formattedMobile);
      
      _reqId = response['req_id'];
      debugPrint('[SERVER OTP] SENT reqId: $_reqId');

      setState(() {
        _isLoading = false;
        _otpSent = true;
      });
      _startCountdown();
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('OTP sent to your phone!')));
      }
    } catch (e) {
      debugPrint('[SERVER OTP] SEND_ERROR: $e');
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: $e'), backgroundColor: Theme.of(context).colorScheme.error));
      }
    }
  }

  void _resendOtp() async {
    if (_countdown > 0) return;
    
    if (_reqId == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Cannot resend without Request ID.')));
      return;
    }

    setState(() => _isLoading = true);
    debugPrint('[SERVER OTP] RETRY_STARTED');
    
    try {
      final repo = ref.read(authRepositoryProvider);
      await repo.resendOtp(_reqId!);
      
      setState(() => _isLoading = false);
      _startCountdown();
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('OTP resent successfully')));
      }
    } catch (e) {
      debugPrint('[SERVER OTP] RETRY_ERROR: $e');
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to resend: $e'), backgroundColor: Theme.of(context).colorScheme.error));
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
    _executeFleetGuardVerification();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _phoneController.dispose();
    _otpController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Phone Verification')),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
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
                        : (widget.companyName != null && widget.companyName!.isNotEmpty)
                            ? 'Joining fleet: ${widget.companyName}'
                            : 'Welcome back to FleetGuard',
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
                    const SizedBox(height: 16),
                    Center(
                      child: Column(
                        children: [
                          if (_countdown > 0)
                            Text(
                              'Resend OTP in $_countdown s',
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.grey),
                            )
                          else
                            TextButton(
                              onPressed: _isLoading ? null : _resendOtp,
                              child: const Text('Resend OTP'),
                            ),
                          TextButton(
                            onPressed: () => setState(() { 
                              _otpSent = false;
                              _reqId = null;
                              _otpController.clear();
                              _countdown = 0;
                              _timer?.cancel();
                            }),
                            child: const Text('Change Phone Number'),
                          ),
                        ],
                      ),
                    ),
                  ],
                  if (!_otpSent && widget.inviteToken == null) ...[
                    const SizedBox(height: 24),
                    const Divider(),
                    const SizedBox(height: 16),
                    Center(
                      child: TextButton.icon(
                        onPressed: () => context.push('/auth/qr-scan'),
                        icon: const Icon(Icons.qr_code_scanner),
                        label: const Text('New Driver? Scan QR Code to Join'),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
