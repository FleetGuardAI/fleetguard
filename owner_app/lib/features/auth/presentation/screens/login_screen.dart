import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../../../core/router/app_router.dart';
import 'package:dio/dio.dart';

import 'dart:convert';
import 'package:mobile_scanner/mobile_scanner.dart';
import 'package:sendotp_flutter_sdk/sendotp_flutter_sdk.dart';
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final MobileScannerController _scannerController = MobileScannerController();
  final _identifierController = TextEditingController();
  final _otpController = TextEditingController();
  
  bool _isLoading = false;
  String? _error;
  bool _hasScanned = false;
  
  bool _isOtpMode = false;
  bool _otpSent = false;
  String? _reqId;
  
  int _countdown = 0;
  Timer? _timer;


  @override
  void initState() {
    super.initState();
    const widgetId = String.fromEnvironment('MSG91_WIDGET_ID', defaultValue: '');
    const widgetToken = String.fromEnvironment('MSG91_WIDGET_TOKEN', defaultValue: '');
    debugPrint('[MSG91 DIAG] initState - widgetId is empty: ${widgetId.isEmpty}');
    if (widgetId.isNotEmpty && widgetToken.isNotEmpty) {
      OTPWidget.initializeWidget(widgetId, widgetToken);
      debugPrint('[MSG91 DIAG] OTPWidget initialized');
    } else {
      debugPrint('[MSG91 DIAG] ERROR: Missing MSG91 environment variables');
    }
  }

  @override
  void dispose() {
    _timer?.cancel();
    _scannerController.dispose();
    _identifierController.dispose();
    _otpController.dispose();
    super.dispose();
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

  Future<void> _loginWithToken(String token) async {
    if (_hasScanned) return;
    
    setState(() {
      _hasScanned = true;
      _isLoading = true;
      _error = null;
    });

    // --- Safe diagnostics (NEVER log actual token) ---
    final api = ref.read(apiClientProvider);
    debugPrint('[QR DIAG] Scanned payload length: ${token.length}');
    debugPrint('[QR DIAG] Payload type: ${token.runtimeType}');
    debugPrint('[QR DIAG] Starts with letter: ${token.isNotEmpty && RegExp(r'^[a-zA-Z0-9]').hasMatch(token)}');
    debugPrint('[QR DIAG] Contains URL scheme: ${token.contains("://")}');
    debugPrint('[QR DIAG] API base URL: ${api.dio.options.baseUrl}');
    debugPrint('[QR DIAG] Target endpoint: /api/v1/auth/owner-qr/verify');

    try {
      final response = await api.dio.post(
        '/api/v1/auth/owner-qr/verify',
        data: {'pairing_token': token.trim()},
      );

      debugPrint('[QR DIAG] HTTP status: ${response.statusCode}');
      debugPrint('[QR DIAG] Response keys: ${response.data?.keys?.toList()}');

      final accessToken = response.data['access_token'];
      final refreshToken = response.data['refresh_token'];
      if (accessToken != null) {
        await SecureStorage.setAccessToken(accessToken);
        if (refreshToken != null) {
          await SecureStorage.setRefreshToken(refreshToken);
        }
        ref.read(authStateProvider.notifier).state = true;
        if (mounted) {
          context.go('/dashboard');
        }
      }
    } on DioException catch (e) {
      debugPrint('[QR DIAG] DioException status: ${e.response?.statusCode}');
      debugPrint('[QR DIAG] DioException detail: ${e.response?.data}');
      debugPrint('[QR DIAG] DioException type: ${e.type}');
      debugPrint('[QR DIAG] Request URI: ${e.requestOptions.uri}');
      setState(() {
        if (e.response == null || e.type == DioExceptionType.connectionTimeout || e.type == DioExceptionType.connectionError) {
          _error = 'Network error: Unable to connect to backend (${e.message}). Please check your connection and API_BASE_URL.';
        } else {
          final detail = e.response?.data?['detail']?.toString() ?? '';
          final lowerDetail = detail.toLowerCase();
          if (lowerDetail.contains('expired')) {
            _error = 'QR code expired. Generate a new QR code and scan again.';
          } else if (lowerDetail.contains('invalid')) {
            _error = 'This QR code is not valid. Generate a new QR code.';
          } else {
            _error = 'Unable to sign in: $detail';
          }
        }
        
        // Wait briefly before allowing another scan to avoid retry storms
        Future.delayed(const Duration(seconds: 2), () {
          if (mounted) {
            setState(() {
              _hasScanned = false;
            });
          }
        });
      });
    } catch (e) {
      debugPrint('[QR DIAG] Unexpected error: ${e.runtimeType}: $e');
      setState(() {
        _error = 'An unexpected error occurred.';
        _hasScanned = false;
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _requestOtp() async {
    final identifier = _identifierController.text.trim();
    if (identifier.isEmpty) return;

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final isEmail = identifier.contains('@');
      
      if (!isEmail) {
        String cleanNum = identifier.replaceAll(RegExp(r'\D'), '');
        if (cleanNum.length == 10) cleanNum = '91$cleanNum';
        
        print('[MSG91 DIAG] SENDING OTP for identifier=$cleanNum');
        
        final response = await OTPWidget.sendOTP({'identifier': cleanNum});
        debugPrint('[MSG91 DIAG] sendOTP response: $response');
        
        if (response == null) {
          throw Exception('OTP Widget not initialized or returned null');
        }
        
        final reqId = response['message'] ?? response['reqId'] ?? identifier;
        debugPrint('[MSG91 DIAG] reqId extracted: $reqId');
        
        setState(() {
          _otpSent = true;
          _reqId = reqId;
        });
        _startCountdown();
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('OTP requested successfully')),
          );
        }
      } else {
        final api = ref.read(apiClientProvider);
        final response = await api.dio.post(
          '/api/v1/auth/request-otp',
          data: {'identifier': identifier},
        );
        
        setState(() {
          _otpSent = true;
          _reqId = response.data['req_id']?.toString() ?? identifier;
        });
        _startCountdown();
        
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('OTP requested successfully')),
          );
        }
      }
    } on DioException catch (e) {
      debugPrint('OTP Request Error: ${e.message}');
      setState(() {
        if (e.response == null || e.type == DioExceptionType.connectionTimeout || e.type == DioExceptionType.connectionError) {
          _error = 'Network error: Unable to connect to backend.';
        } else {
          _error = e.response?.data?['detail']?.toString() ?? 'Failed to send OTP.';
        }
      });
    } catch (e) {
      debugPrint('OTP Request Error: $e');
      setState(() {
        _error = 'Unable to send OTP. Please check your mobile number and try again.';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _resendOtp() async {
    if (_countdown > 0) return;

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final identifier = _identifierController.text.trim();
      final isEmail = identifier.contains('@');

      if (!isEmail) {
        await OTPWidget.retryOTP({'retryChannel': 1, 'reqId': _reqId});
      } else {
        final api = ref.read(apiClientProvider);
        await api.dio.post(
          '/api/v1/auth/request-otp',
          data: {'identifier': identifier},
        );
      }
      
      _startCountdown();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('OTP resent successfully')),
        );
      }
    } on DioException catch (e) {
      debugPrint('OTP Resend Error: ${e.message}');
      setState(() {
        if (e.response == null || e.type == DioExceptionType.connectionTimeout || e.type == DioExceptionType.connectionError) {
          _error = 'Network error: Unable to connect to backend.';
        } else {
          _error = e.response?.data?['detail']?.toString() ?? 'Failed to resend OTP.';
        }
      });
    } catch (e) {
      debugPrint('OTP Resend Error: $e');
      setState(() {
        _error = 'OTP service temporarily unavailable. Please try again later.';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _verifyOtp() async {
    final identifier = _identifierController.text.trim();
    final otp = _otpController.text.trim();
    if (otp.isEmpty || identifier.isEmpty) return;

    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final isEmail = identifier.contains('@');
      String? msg91Token;
      
      if (!isEmail) {
        final response = await OTPWidget.verifyOTP({'otp': otp, 'reqId': _reqId});
        if (response != null) {
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
          if (msg91Token == null) {
             msg91Token = jsonEncode(response);
          }
        }
      }

      final api = ref.read(apiClientProvider);
      final response = await api.dio.post(
        '/api/v1/auth/verify-otp',
        data: {
          'identifier': identifier, 
          'req_id': _reqId ?? identifier, 
          'code': isEmail ? otp : '123456', 
          'msg91_token': msg91Token,
        },
      );

      final accessToken = response.data['access_token'];
      final refreshToken = response.data['refresh_token'];
      if (accessToken != null) {
        await SecureStorage.setAccessToken(accessToken);
        if (refreshToken != null) {
          await SecureStorage.setRefreshToken(refreshToken);
        }
        ref.read(authStateProvider.notifier).state = true;
        if (mounted) {
          context.go('/dashboard');
        }
      }
    } on DioException catch (e) {
      debugPrint('Backend Verify Error: ${e.message}');
      setState(() {
        if (e.response == null || e.type == DioExceptionType.connectionTimeout || e.type == DioExceptionType.connectionError) {
          _error = 'Network error: Unable to connect to backend.';
        } else {
          _error = e.response?.data?['detail']?.toString() ?? 'Invalid OTP. Please try again.';
        }
      });
    } catch (e) {
      debugPrint('OTP Verify Error: $e');
      setState(() {
        _error = 'Invalid OTP. Please try again.';
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 24),
            Text(
              'Owner Login',
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            
            // Mode Toggle
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24.0),
              child: Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        backgroundColor: !_isOtpMode ? Theme.of(context).primaryColor.withValues(alpha: 0.1) : null,
                      ),
                      onPressed: () => setState(() => _isOtpMode = false),
                      child: const Text('Scan QR Code'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: OutlinedButton(
                      style: OutlinedButton.styleFrom(
                        backgroundColor: _isOtpMode ? Theme.of(context).primaryColor.withValues(alpha: 0.1) : null,
                      ),
                      onPressed: () => setState(() => _isOtpMode = true),
                      child: const Text('Use OTP'),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            if (!_isOtpMode) ...[
              const Padding(
                padding: EdgeInsets.symmetric(horizontal: 24.0),
                child: Text(
                  'Scan the QR code from the FleetGuard Dashboard to log in.',
                  textAlign: TextAlign.center,
                ),
              ),
              const SizedBox(height: 16),
              Expanded(
                child: Stack(
                  children: [
                    MobileScanner(
                      controller: _scannerController,
                      onDetect: (capture) {
                        if (_hasScanned) return;
                        final List<Barcode> barcodes = capture.barcodes;
                        for (final barcode in barcodes) {
                          if (barcode.rawValue != null) {
                            _loginWithToken(barcode.rawValue!);
                            break;
                          }
                        }
                      },
                    ),
                    if (_isLoading)
                      Container(
                        color: Colors.black54,
                        child: const Center(
                          child: CircularProgressIndicator(),
                        ),
                      ),
                  ],
                ),
              ),
            ] else ...[
              // OTP Mode
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      TextField(
                        controller: _identifierController,
                        decoration: const InputDecoration(
                          labelText: 'Email or Mobile Number',
                          border: OutlineInputBorder(),
                        ),
                        enabled: !_otpSent && !_isLoading,
                      ),
                      const SizedBox(height: 16),
                      if (_otpSent)
                        TextField(
                          controller: _otpController,
                          decoration: const InputDecoration(
                            labelText: 'OTP Code',
                            border: OutlineInputBorder(),
                          ),
                          enabled: !_isLoading,
                        ),
                      const SizedBox(height: 24),
                      SizedBox(
                        width: double.infinity,
                        height: 48,
                        child: ElevatedButton(
                          onPressed: _isLoading
                              ? null
                              : (_otpSent ? _verifyOtp : _requestOtp),
                          child: _isLoading
                              ? const CircularProgressIndicator()
                              : Text(_otpSent ? 'Verify OTP' : 'Request OTP'),
                        ),
                      ),
                      if (_otpSent) ...[
  const SizedBox(height: 16),

  if (_countdown > 0)
    Text(
      'Resend OTP in $_countdown s',
      style: Theme.of(context)
          .textTheme
          .bodySmall
          ?.copyWith(color: Colors.grey),
    )
  else
    TextButton(
      onPressed: _isLoading ? null : _resendOtp,
      child: const Text('Resend OTP'),
    ),

  TextButton(
    onPressed: () {
      setState(() {
        _otpSent = false;
        _otpController.clear();
        _reqId = null;
        _error = null;
        _countdown = 0;
        _timer?.cancel();
      });
    },
    child: const Text('Change identifier'),
  ),
],
            
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Text(
                    _error!,
                    style: const TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                    textAlign: TextAlign.center,
                  ),
                ),
            ], // Close Column children
          ), // Close Column
        ), // Close Padding
      ), // Close Expanded
    ], // Close else spread
    if (!_isOtpMode) const SizedBox(height: 48),
  ], // Close main Column children
), // Close main Column
), // Close SafeArea
); // Close Scaffold
}
}
