import 'package:flutter/material.dart';

class WalletScreen extends StatelessWidget {
  const WalletScreen({super.key});

  void _showAdvanceDialog(BuildContext context) {
    final amountController = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Request Salary Advance'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Enter advance amount requested for approval from fleet manager:'),
            const SizedBox(height: 12),
            TextField(
              controller: amountController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Amount (₹)', prefixIcon: Icon(Icons.currency_rupee)),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Salary advance request submitted for fleet manager approval!')),
              );
            },
            child: const Text('Submit Request'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Driver Wallet')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Balance Card
            Card(
              color: Theme.of(context).colorScheme.primary,
              child: Padding(
                padding: const EdgeInsets.all(24.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Available Wallet Balance', style: TextStyle(color: Colors.white70, fontSize: 14)),
                    const SizedBox(height: 8),
                    const Text('₹ 14,500.00', style: TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 20),
                    Row(
                      children: [
                        Expanded(
                          child: ElevatedButton.icon(
                            style: ElevatedButton.styleFrom(backgroundColor: Colors.white, foregroundColor: Colors.black),
                            onPressed: () => _showAdvanceDialog(context),
                            icon: const Icon(Icons.request_quote),
                            label: const Text('Request Advance'),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildSummaryTile(context, 'Monthly Salary', '₹22,000', Colors.blue),
                _buildSummaryTile(context, 'Total Advances', '₹8,000', Colors.orange),
                _buildSummaryTile(context, 'Incentives', '₹2,500', Colors.green),
              ],
            ),
            const SizedBox(height: 24),
            Text('Recent Transactions', style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 12),
            const Card(
              child: ListTile(
                leading: CircleAvatar(backgroundColor: Colors.green, child: Icon(Icons.arrow_downward, color: Colors.white)),
                title: Text('July Salary Disbursed', style: TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text('Direct Bank Transfer • 28 July 2026'),
                trailing: Text('+₹22,000', style: TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
              ),
            ),
            const Card(
              child: ListTile(
                leading: CircleAvatar(backgroundColor: Colors.orange, child: Icon(Icons.arrow_upward, color: Colors.white)),
                title: Text('Trip Advance — Mumbai Route', style: TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text('Approved Advance • 24 July 2026'),
                trailing: Text('-₹5,000', style: TextStyle(color: Colors.orange, fontWeight: FontWeight.bold)),
              ),
            ),
            const Card(
              child: ListTile(
                leading: CircleAvatar(backgroundColor: Colors.blue, child: Icon(Icons.star, color: Colors.white)),
                title: Text('On-Time Delivery Incentive', style: TextStyle(fontWeight: FontWeight.bold)),
                subtitle: Text('Safety & ETA Bonus • 20 July 2026'),
                trailing: Text('+₹2,500', style: TextStyle(color: Colors.blue, fontWeight: FontWeight.bold)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryTile(BuildContext context, String title, String amount, Color color) {
    return Column(
      children: [
        Text(title, style: const TextStyle(color: Colors.grey, fontSize: 12)),
        const SizedBox(height: 4),
        Text(amount, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: color)),
      ],
    );
  }
}
