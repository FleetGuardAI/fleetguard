import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/config/theme/app_colors.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/network/api_endpoints.dart';

class EmergencyScreen extends ConsumerStatefulWidget {
  const EmergencyScreen({super.key});

  @override
  ConsumerState<EmergencyScreen> createState() => _EmergencyScreenState();
}

class _EmergencyScreenState extends ConsumerState<EmergencyScreen> {
  bool _sosTriggered = false;
  bool _loading = false;
  String? _activeTicketId;

  Future<void> _triggerSos() async {
    setState(() => _loading = true);

    try {
      final response = await ref.read(apiClientProvider).post(
        ApiEndpoints.sos,
        data: {
          'message': 'EMERGENCY SOS: Driver triggered panic alert from mobile app',
        },
      );

      if (mounted) {
        final ticketId = response.data['ticket_id'] ?? 'SOS-ACTIVE';
        setState(() {
          _sosTriggered = true;
          _activeTicketId = ticketId;
          _loading = false;
        });

        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('🚨 SOS DISPATCHED ($ticketId)! Live tracking shared with Fleet Control & Super Admin.'),
            backgroundColor: Colors.red.shade700,
            duration: const Duration(seconds: 6),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _loading = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to transmit SOS: $e'),
            backgroundColor: Colors.red.shade900,
          ),
        );
      }
    }
  }

  void _showAssistanceDialog() {
    final titleController = TextEditingController();
    final descController = TextEditingController();
    bool submitting = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: const Text('Request Assistance'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: titleController,
                  decoration: const InputDecoration(
                    labelText: 'Issue Summary',
                    hintText: 'e.g. Flat tyre, engine light, document issue',
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: descController,
                  maxLines: 3,
                  decoration: const InputDecoration(
                    labelText: 'Details',
                    hintText: 'Provide details about your current situation...',
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(backgroundColor: AppColors.primary),
              onPressed: submitting
                  ? null
                  : () async {
                      if (titleController.text.trim().isEmpty || descController.text.trim().isEmpty) return;
                      setDialogState(() => submitting = true);
                      try {
                        final res = await ref.read(apiClientProvider).post(
                          ApiEndpoints.assistance,
                          data: {
                            'title': titleController.text.trim(),
                            'description': descController.text.trim(),
                            'category': 'TECHNICAL',
                            'priority': 'HIGH',
                          },
                        );
                        if (mounted) {
                          Navigator.pop(ctx);
                          final ticketId = res.data['ticket_id'] ?? 'Assistance';
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text('Assistance Ticket Created ($ticketId). Support will respond shortly.'),
                              backgroundColor: Colors.green.shade700,
                            ),
                          );
                        }
                      } catch (err) {
                        setDialogState(() => submitting = false);
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text('Failed to submit: $err'),
                              backgroundColor: Colors.red,
                            ),
                          );
                        }
                      }
                    },
              child: submitting
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Submit Request', style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Emergency Assistance'),
        actions: [
          IconButton(
            icon: const Icon(Icons.help_outline),
            tooltip: 'Request Support',
            onPressed: _showAssistanceDialog,
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          children: [
            const SizedBox(height: 16),
            Text(
              _sosTriggered ? 'EMERGENCY ALERT ACTIVE' : 'Emergency SOS Button',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: _sosTriggered ? Colors.red : null,
                  ),
            ),
            if (_activeTicketId != null) ...[
              const SizedBox(height: 4),
              Text(
                'Incident Ref: $_activeTicketId',
                style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.red, fontSize: 13),
              ),
            ],
            const SizedBox(height: 12),
            Text(
              _sosTriggered
                  ? 'Your live location, truck info, and active trip details are currently open in the Fleet & Super Admin emergency queues.'
                  : 'Press and hold the SOS button in case of accident, breakdown, or security emergency.',
              textAlign: TextAlign.center,
              style: const TextStyle(color: Colors.grey),
            ),
            const Spacer(),
            Center(
              child: GestureDetector(
                onLongPress: (_sosTriggered || _loading) ? null : _triggerSos,
                onTap: _sosTriggered
                    ? null
                    : () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Press and HOLD SOS button for 1 second to dispatch emergency alert')),
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
                        color: Colors.red.withValues(alpha: 0.4),
                        blurRadius: 30,
                        spreadRadius: 10,
                      ),
                    ],
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (_loading)
                        const CircularProgressIndicator(color: Colors.white)
                      else ...[
                        const Icon(Icons.sos, size: 70, color: Colors.white),
                        const SizedBox(height: 8),
                        Text(
                          _sosTriggered ? 'ACTIVE' : 'HOLD FOR SOS',
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                      ],
                    ],
                  ),
                ),
              ),
            ),
            const Spacer(),
            if (_sosTriggered)
              OutlinedButton.icon(
                style: OutlinedButton.styleFrom(foregroundColor: Colors.green),
                onPressed: () => setState(() {
                  _sosTriggered = false;
                  _activeTicketId = null;
                }),
                icon: const Icon(Icons.check),
                label: const Text('Mark Emergency Resolved'),
              )
            else
              OutlinedButton.icon(
                icon: const Icon(Icons.support_agent),
                label: const Text('Need Non-Emergency Assistance?'),
                onPressed: _showAssistanceDialog,
              ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }
}
