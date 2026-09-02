import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'dart:convert';
import '../../../../core/config/app_config.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../../../core/utils/validators.dart';
import '../../data/auth_repository.dart';
import 'package:sendotp_flutter_sdk/sendotp_flutter_sdk.dart';

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
  String? _reqId;
  
  bool _msg91InitError = false;
  
  int _countdown = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _initMsg91();
  }

  void _initMsg91() {
    final widgetId = AppConfig.msg91MobileWidgetId;
    final widgetToken = AppConfig.msg91MobileWidgetToken;
    
    if (widgetId.isEmpty || widgetToken.isEmpty) {
      debugPrint('[MSG91 MOBILE] ERROR: Missing MSG91_MOBILE_WIDGET_ID or MSG91_MOBILE_WIDGET_TOKEN');
      setState(() {
        _msg91InitError = true;
      });
      return;
    }
    
    try {
      OTPWidget.initializeWidget(widgetId, widgetToken);
      debugPrint('[MSG91 MOBILE] INITIALIZED');
    } catch (e) {
      debugPrint('[MSG91 MOBILE] ERROR during initialization: $e');
      setState(() {
        _msg91InitError = true;
      });
    }
  }

  void _executeFleetGuardVerification(String msg91Token) async {
    try {
      final repo = ref.read(authRepositoryProvider);
      final response = await repo.verifyOtp(
        _phoneController.text.trim(), 
        _reqId ?? 'widget-req',
        _otpController.text.trim(), 
        widget.inviteToken,
        msg91Token,
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
      if (widget.companyName.isNotEmpty) {
        await SecureStorage.setCompanyName(widget.companyName);
      }
      // Store invite token for session persistence
      await SecureStorage.setInviteToken(widget.inviteToken);

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
          SnackBar(content: Text('FleetGuard verification failed: $e'), backgroundColor: Theme.of(context).colorScheme.error),
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
    
    if (_msg91InitError) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Mobile OTP configuration is missing.')));
      return;
    }

    setState(() => _isLoading = true);
    debugPrint('[MSG91 MOBILE] SEND_STARTED');
    
    String phone = _phoneController.text.trim();
    String formattedMobile = phone.replaceAll(RegExp(r'\D'), '');
    if (formattedMobile.length == 10) {
      formattedMobile = '91$formattedMobile';
    }
    
    try {
      final response = await OTPWidget.sendOTP({
        'identifier': formattedMobile,
      });
      
      if (response != null && response['type'] != 'error') {
        debugPrint('[MSG91 MOBILE] SEND_SUCCESS, keys: ${response.keys.toList()}');
        setState(() {
          _isLoading = false;
          _otpSent = true;
          // Extract reqId correctly based on actual response structure
          _reqId = response['message']?.toString() ?? response['reqId']?.toString() ?? 'unknown_req';
        });
        _startCountdown();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('OTP sent to your phone!')));
        }
      } else {
        debugPrint('[MSG91 MOBILE] SEND_ERROR');
        setState(() => _isLoading = false);
        if (mounted) {
          final errMsg = response?['message'] ?? 'Unknown error';
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: $errMsg'), backgroundColor: Theme.of(context).colorScheme.error));
        }
      }
    } catch (e) {
      debugPrint('[MSG91 MOBILE] SEND_ERROR');
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e'), backgroundColor: Theme.of(context).colorScheme.error));
      }
    }
  }

  void _resendOtp() async {
    if (_countdown > 0) return;
    
    if (_msg91InitError) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Mobile OTP configuration is missing.')));
      return;
    }

    if (_reqId == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Cannot resend without Request ID.')));
      return;
    }

    setState(() => _isLoading = true);
    debugPrint('[MSG91 MOBILE] RETRY_STARTED');
    
    try {
      final response = await OTPWidget.retryOTP({
        'reqId': _reqId,
      });
      
      if (response != null && response['type'] != 'error') {
        debugPrint('[MSG91 MOBILE] RETRY_SUCCESS');
        setState(() => _isLoading = false);
        _startCountdown();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('OTP resent successfully')));
        }
      } else {
        debugPrint('[MSG91 MOBILE] RETRY_ERROR');
        setState(() => _isLoading = false);
        if (mounted) {
          final errMsg = response?['message'] ?? 'Unknown error';
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: $errMsg'), backgroundColor: Theme.of(context).colorScheme.error));
        }
      }
    } catch (e) {
      debugPrint('[MSG91 MOBILE] RETRY_ERROR');
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e'), backgroundColor: Theme.of(context).colorScheme.error));
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

    if (_msg91InitError) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Mobile OTP configuration is missing.')));
      return;
    }

    setState(() => _isLoading = true);
    debugPrint('[MSG91 MOBILE] VERIFY_STARTED');
    
    try {
      final response = await OTPWidget.verifyOTP({
        'reqId': _reqId,
        'otp': _otpController.text.trim(),
      });
      
      if (response != null && response['type'] != 'error') {
        debugPrint('[MSG91 MOBILE] VERIFY_SUCCESS, keys: ${response.keys.toList()}');
        
        String msg91Token = '';
        if (response['message'] is String && response['type'] != 'error') {
          msg91Token = response['message'];
        } else if (response['token'] is String) {
          msg91Token = response['token'];
        } else if (response['access_token'] is String) {
          msg91Token = response['access_token'];
        } else if (response['jwt'] is String) {
          msg91Token = response['jwt'];
        } else if (response['data'] is String) {
          msg91Token = response['data'];
        }
        
        if (msg91Token.isEmpty) {
          msg91Token = jsonEncode(response);
        }
        
        _executeFleetGuardVerification(msg91Token);
      } else {
        debugPrint('[MSG91 MOBILE] VERIFY_ERROR');
        setState(() => _isLoading = false);
        if (mounted) {
          final errMsg = response?['message'] ?? 'Unknown error';
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: $errMsg'), backgroundColor: Theme.of(context).colorScheme.error));
        }
      }
    } catch (e) {
      debugPrint('[MSG91 MOBILE] VERIFY_ERROR');
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e'), backgroundColor: Theme.of(context).colorScheme.error));
      }
    }
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
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
