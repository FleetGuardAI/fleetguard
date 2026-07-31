import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class InspectionScreen extends StatefulWidget {
  final String type; // PRE_TRIP or POST_TRIP

  const InspectionScreen({super.key, required this.type});

  @override
  State<InspectionScreen> createState() => _InspectionScreenState();
}

class _InspectionScreenState extends State<InspectionScreen> {
  final Map<String, bool> _checklist = {
    'Tyres': true,
    'Brakes': true,
    'Mirrors': true,
    'Horn': true,
    'Lights': true,
    'Leaks': true,
    'Battery': true,
  };

  bool _isSubmitting = false;

  void _submitInspection() async {
    setState(() => _isSubmitting = true);
    await Future.delayed(const Duration(seconds: 1));
    setState(() => _isSubmitting = false);

    final hasFailed = _checklist.values.any((passed) => !passed);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            hasFailed
                ? 'Inspection submitted. Maintenance ticket auto-generated for failed items!'
                : '${widget.type} inspection passed successfully!',
          ),
          backgroundColor: hasFailed ? Colors.orange : Colors.green,
        ),
      );
      context.pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('${widget.type} Inspection')),
      body: Column(
        children: [
          Container(
            color: Theme.of(context).colorScheme.primaryContainer.withOpacity(0.3),
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                const Icon(Icons.fact_check, color: Colors.blue, size: 32),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('${widget.type} Checklist', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      const Text('Verify all vehicle safety components before departure.', style: TextStyle(fontSize: 12)),
                    ],
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: _checklist.keys.map((item) {
                final passed = _checklist[item]!;
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: SwitchListTile(
                    title: Text(item, style: const TextStyle(fontWeight: FontWeight.bold)),
                    subtitle: Text(passed ? 'Condition: PASS' : 'Condition: FAIL (Auto-Ticket)'),
                    value: passed,
                    activeColor: Colors.green,
                    inactiveThumbColor: Colors.red,
                    onChanged: (val) => setState(() => _checklist[item] = val),
                  ),
                );
              }).toList(),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _isSubmitting ? null : _submitInspection,
                child: _isSubmitting ? const CircularProgressIndicator() : const Text('Submit Inspection Report'),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
