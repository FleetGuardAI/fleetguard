import React, { useEffect, useRef, useState } from 'react';

export default function DriverOtpBridge() {
  const [status, setStatus] = useState('Initializing Bridge...');
  const configurationRef = useRef(null);
  
  const sendMessageToFlutter = (event, data = null) => {
    const payload = JSON.stringify({ event, data });
    console.log('[BRIDGE DEBUG] Sending to Flutter:', payload);
    if (window.Msg91Channel && window.Msg91Channel.postMessage) {
      window.Msg91Channel.postMessage(payload);
    }
  };

  useEffect(() => {
    // Expose global methods for Flutter to invoke
    window.invokeSendOtp = (mobile) => {
      console.log('[BRIDGE DEBUG] invokeSendOtp called', mobile);
      if (!window.sendOtp) {
        sendMessageToFlutter('OTP_ERROR', 'Widget not fully initialized');
        return;
      }
      sendMessageToFlutter('SEND_OTP_CALLED');
      window.sendOtp(
        mobile,
        (data) => sendMessageToFlutter('OTP_SENT', data),
        (err) => sendMessageToFlutter('OTP_ERROR', err)
      );
    };

    window.invokeVerifyOtp = (otp) => {
      console.log('[BRIDGE DEBUG] invokeVerifyOtp called', otp);
      if (!window.verifyOtp) {
        sendMessageToFlutter('OTP_ERROR', 'Widget not fully initialized');
        return;
      }
      window.verifyOtp(
        otp,
        (data) => sendMessageToFlutter('OTP_VERIFIED', data),
        (err) => sendMessageToFlutter('OTP_ERROR', err)
      );
    };

    window.invokeRetryOtp = () => {
      console.log('[BRIDGE DEBUG] invokeRetryOtp called');
      if (!window.retryOtp) {
        sendMessageToFlutter('OTP_ERROR', 'Widget not fully initialized');
        return;
      }
      window.retryOtp(
        (data) => sendMessageToFlutter('retryOtpSuccess', data),
        (err) => sendMessageToFlutter('OTP_ERROR', err)
      );
    };

    // Load MSG91 script
    if (!document.getElementById('msg91-widget-script-bridge')) {
      const script = document.createElement('script');
      script.id = 'msg91-widget-script-bridge';
      script.src = 'https://control.msg91.com/app/assets/widget/chat-widget.js';
      script.async = true;
      script.onload = () => {
        sendMessageToFlutter('MSG91_SCRIPT_LOADED');
        setStatus('Script loaded, initializing widget...');
        
        configurationRef.current = {
          widgetId: import.meta.env.VITE_MSG91_WIDGET_ID,
          tokenAuth: import.meta.env.VITE_MSG91_WIDGET_TOKEN,
          exposeMethods: true,
          success: (data) => sendMessageToFlutter('OTP_VERIFIED', data),
          failure: (error) => sendMessageToFlutter('OTP_ERROR', error)
        };
        
        const checkReady = () => {
          if (window.sendOtp && window.initSendOTP) {
            try {
              window.initSendOTP(configurationRef.current);
              sendMessageToFlutter('WIDGET_READY');
              setStatus('Bridge Ready');
            } catch (err) {
              sendMessageToFlutter('OTP_ERROR', 'Init failed: ' + err.message);
              setStatus('Initialization Failed');
            }
          } else {
            setTimeout(checkReady, 100);
          }
        };
        checkReady();
      };
      
      script.onerror = () => {
        sendMessageToFlutter('OTP_ERROR', 'Failed to load MSG91 script');
        setStatus('Script Load Error');
      };
      
      document.body.appendChild(script);
    }
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h3>Driver OTP Bridge</h3>
      <p>Status: {status}</p>
      {/* Expose buttons for manual testing in Chrome */}
      <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
        <button onClick={() => window.invokeSendOtp && window.invokeSendOtp('919876543210')}>
          Test sendOtp
        </button>
        <button onClick={() => window.invokeVerifyOtp && window.invokeVerifyOtp('123456')}>
          Test verifyOtp
        </button>
      </div>
    </div>
  );
}
