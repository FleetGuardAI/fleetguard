import 'package:flutter/material.dart';

import '../../../../core/config/theme/app_colors.dart';

class EmergencyScreen extends StatefulWidget {
  const EmergencyScreen({super.key});

  @override
  State<EmergencyScreen> createState() => _EmergencyScreenState();
}

class _EmergencyScreenState extends State<EmergencyScreen> {
  bool _sosTriggered = false;

  void _triggerSos() async {
    setState(() => _sosTriggered = true);
    await Future.delayed(const Duration(seconds: 1));

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('🚨 EMERGENCY SOS SENT! Live location shared with Fleet Manager & Emergency Response.'),
          backgroundColor: Colors.red,
          duration: Duration(seconds: 5),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Emergency Assistance')),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            const SizedBox(height: 20),
            Text(
              _sosTriggered ? 'EMERGENCY ALERT ACTIVE' : 'Emergency SOS Button',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: _sosTriggered ? Colors.red : null,
                  ),
            ),
            const SizedBox(height: 12),
            Text(
              _sosTriggered
                  ? 'Your live location, truck info (MH-12-FG-2026), and active trip details are being transmitted to the fleet control center.'
                  : 'Press and hold the SOS button in case of accident, breakdown, or security emergency.',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.grey),
            ),
            const Spacer(),
            Center(
              child: GestureDetector(
                onLongPress: _sosTriggered ? null : _triggerSos,
                onTap: _sosTriggered
                    ? null
                    : () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Press and HOLD SOS button to activate emergency alert')),
                        );
                      },
                child: Container(
                  width: 200,
                  height: 200,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: AppColors.dangerGradient,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.red.withOpacity(0.4),
                        blurRadius: 30,
                        spreadRadius: 10,
                      ),
                    ],
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.sos, size: 70, color: Colors.white),
                      const SizedBox(height: 8),
                      Text(
                        _sosTriggered ? 'ACTIVE' : 'HOLD FOR SOS',
                        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const Spacer(),
            if (_sosTriggered)
              OutlinedButton.icon(
                style: OutlinedButton.styleFrom(foregroundColor: Colors.green),
                onPressed: () => setState(() => _sosTriggered = false),
                icon: const Icon(Icons.check),
                label: const Text('Mark Emergency Resolved'),
              ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
