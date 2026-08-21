import 'dart:async';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'dart:convert';
import '../../../../core/config/app_config.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../../../core/utils/validators.dart';
import '../../data/auth_repository.dart';
import 'package:webview_flutter/webview_flutter.dart';

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
  
  late final WebViewController _webViewController;
  bool _isMsg91WidgetReady = false;
  bool _msg91InitError = false;
  Timer? _initTimer;
  
  int _countdown = 0;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _initWebView();
  }

  void _initWebView() {
    debugPrint('[MSG91 DEBUG] WEBVIEW_CREATED');
    _webViewController = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0x00000000))
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageFinished: (_) {
            debugPrint('[MSG91 DEBUG] HTML_LOADED');
          },
        ),
      )
      ..addJavaScriptChannel(
        'Msg91Channel',
        onMessageReceived: (JavaScriptMessage message) {
          _handleMsg91Event(message.message);
        },
      )
      ..loadHtmlString(_buildMsg91Html());
      
    _initTimer = Timer(const Duration(seconds: 15), () {
      if (!_isMsg91WidgetReady && mounted) {
        setState(() {
          _msg91InitError = true;
        });
        debugPrint('[MSG91 DEBUG] ERROR: Widget initialization timed out');
      }
    });
  }

  String _buildMsg91Html() {
    return """
      <!DOCTYPE html>
      <html>
      <head>
        <script>
          function scriptLoaded() {
            Msg91Channel.postMessage(JSON.stringify({ event: 'MSG91_SCRIPT_LOADED' }));
          }
          function checkWidgetReady() {
             if (window.sendOtp && window.initSendOTP) {
                const configuration = {
                  widgetId: '${AppConfig.msg91WidgetId}',
                  tokenAuth: '${AppConfig.msg91WidgetToken}',
                  exposeMethods: true,
                  success: function(data) { Msg91Channel.postMessage(JSON.stringify({ event: 'OTP_VERIFIED', data: data })); },
                  failure: function(error) { Msg91Channel.postMessage(JSON.stringify({ event: 'OTP_ERROR', data: error })); }
                };
                try {
                  window.initSendOTP(configuration);
                  Msg91Channel.postMessage(JSON.stringify({ event: 'WIDGET_READY' }));
                } catch (e) {
                  Msg91Channel.postMessage(JSON.stringify({ event: 'OTP_ERROR', data: 'Init failed' }));
                }
             } else {
                setTimeout(checkWidgetReady, 100);
             }
          }
          window.onload = function() {
            checkWidgetReady();
          };
        </script>
        <script type="text/javascript" src="https://control.msg91.com/app/assets/widget/chat-widget.js" onload="scriptLoaded()"></script>
        <script>
          function invokeSendOtp(mobile) {
            if(!window.sendOtp) {
               Msg91Channel.postMessage(JSON.stringify({ event: 'OTP_ERROR', data: 'Widget not initialized' }));
               return;
            }
            Msg91Channel.postMessage(JSON.stringify({ event: 'SEND_OTP_CALLED' }));
            window.sendOtp(mobile, 
              function(data) { Msg91Channel.postMessage(JSON.stringify({ event: 'OTP_SENT', data: data })); },
              function(error) { Msg91Channel.postMessage(JSON.stringify({ event: 'OTP_ERROR', data: error })); }
            );
          }

          function invokeVerifyOtp(otp) {
            window.verifyOtp(otp,
              function(data) { Msg91Channel.postMessage(JSON.stringify({ event: 'OTP_VERIFIED', data: data })); },
              function(error) { Msg91Channel.postMessage(JSON.stringify({ event: 'OTP_ERROR', data: error })); }
            );
          }

          function invokeRetryOtp() {
            window.retryOtp(
              function(data) { Msg91Channel.postMessage(JSON.stringify({ event: 'retryOtpSuccess', data: data })); },
              function(error) { Msg91Channel.postMessage(JSON.stringify({ event: 'OTP_ERROR', data: error })); }
            );
          }
        </script>
      </head>
      <body></body>
      </html>
    """;
  }

  void _handleMsg91Event(String message) {
    try {
      final parsed = jsonDecode(message);
      final event = parsed['event'];
      final data = parsed['data'];

      if (event == 'MSG91_SCRIPT_LOADED') {
        debugPrint('[MSG91 DEBUG] MSG91_SCRIPT_LOADED');
      } else if (event == 'WIDGET_READY') {
        debugPrint('[MSG91 DEBUG] WIDGET_READY');
        setState(() => _isMsg91WidgetReady = true);
        _initTimer?.cancel();
      } else if (event == 'SEND_OTP_CALLED') {
        debugPrint('[MSG91 DEBUG] SEND_OTP_CALLED');
      } else if (event == 'OTP_SENT') {
        debugPrint('[MSG91 DEBUG] OTP_SENT');
        setState(() {
          _isLoading = false;
          _otpSent = true;
          _reqId = data != null ? (data['message'] ?? data['reqId']) : 'widget-req';
        });
        _startCountdown();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('OTP sent to your phone!')));
        }
      } else if (event == 'OTP_ERROR') {
        debugPrint('[MSG91 DEBUG] OTP_ERROR');
        setState(() => _isLoading = false);
        if (mounted) {
          final errMsg = data != null ? (data['message'] ?? data.toString()) : 'Unknown error';
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed: $errMsg'), backgroundColor: Theme.of(context).colorScheme.error));
        }
      } else if (event == 'OTP_VERIFIED') {
        debugPrint('[MSG91 DEBUG] OTP_VERIFIED');
        String msg91Token = '';
        if (data is String) {
          msg91Token = data;
        } else if (data is Map) {
          if (data['message'] is String && data['type'] != 'error') {
            msg91Token = data['message'];
          } else if (data['token'] is String) {
            msg91Token = data['token'];
          } else if (data['access_token'] is String) {
            msg91Token = data['access_token'];
          } else if (data['jwt'] is String) {
            msg91Token = data['jwt'];
          } else if (data['data'] is String) {
            msg91Token = data['data'];
          }
        }
        if (msg91Token.isEmpty) {
          msg91Token = jsonEncode(data);
        }
        
        _executeFleetGuardVerification(msg91Token);
      } else if (event == 'verifyOtpFailure') {
        setState(() => _isLoading = false);
        if (mounted) {
          final errMsg = data != null ? (data['message'] ?? data.toString()) : 'Unknown error';
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to verify OTP: $errMsg'), backgroundColor: Theme.of(context).colorScheme.error));
        }
      } else if (event == 'retryOtpSuccess') {
        setState(() => _isLoading = false);
        _startCountdown();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('OTP resent successfully')));
        }
      } else if (event == 'retryOtpFailure') {
        setState(() => _isLoading = false);
        if (mounted) {
          final errMsg = data != null ? (data['message'] ?? data.toString()) : 'Unknown error';
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to resend OTP: $errMsg'), backgroundColor: Theme.of(context).colorScheme.error));
        }
      }
    } catch (e) {
      debugPrint('Error parsing Msg91 message: $e');
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

      setState(() => _isLoading = false);

      if (mounted) {
        if (response['is_new_driver'] == true || response['verification_status'] != 'APPROVED') {
          context.go('/auth/profile');
        } else {
          context.go('/home');
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
    
    if (!_isMsg91WidgetReady) {
      if (_msg91InitError) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Unable to initialize OTP service')));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('OTP service is still loading. Please wait a moment and try again.')));
      }
      return;
    }

    setState(() => _isLoading = true);
    
    String phone = _phoneController.text.trim();
    String formattedMobile = phone.replaceAll(RegExp(r'\D'), '');
    if (formattedMobile.length == 10) {
      formattedMobile = '91$formattedMobile';
    }
    
    _webViewController.runJavaScript("invokeSendOtp('$formattedMobile');");
  }

  void _resendOtp() async {
    if (_countdown > 0) return;
    
    if (!_isMsg91WidgetReady) {
      if (_msg91InitError) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Unable to initialize OTP service')));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('OTP service is still loading. Please wait a moment and try again.')));
      }
      return;
    }

    setState(() => _isLoading = true);
    _webViewController.runJavaScript("invokeRetryOtp();");
  }

  void _verifyOtp() async {
    if (_otpController.text.trim().length != 6) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Invalid OTP length.')),
      );
      return;
    }

    if (!_isMsg91WidgetReady) {
      if (_msg91InitError) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Unable to initialize OTP service')));
      } else {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('OTP service is still loading. Please wait a moment and try again.')));
      }
      return;
    }

    setState(() => _isLoading = true);
    _webViewController.runJavaScript("invokeVerifyOtp('${_otpController.text.trim()}');");
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
      body: Stack(
        children: [
          // Invisible WebView for MSG91 Widget
          SizedBox(
            width: 1,
            height: 1,
            child: WebViewWidget(controller: _webViewController),
          ),
          Padding(
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
        ],
      ),
    );
  }
}
