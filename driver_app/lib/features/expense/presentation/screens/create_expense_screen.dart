import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

import '../../../../core/utils/validators.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../data/expense_repository.dart';
import '../providers/expense_provider.dart';

class CreateExpenseScreen extends ConsumerStatefulWidget {
  const CreateExpenseScreen({super.key});

  @override
  ConsumerState<CreateExpenseScreen> createState() => _CreateExpenseScreenState();
}

class _CreateExpenseScreenState extends ConsumerState<CreateExpenseScreen> {
  final _amountController = TextEditingController();
  final _vendorController = TextEditingController();
  final _gstController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  String _category = 'FUEL';
  bool _isOcrProcessing = false;
  bool _isSubmitting = false;

  void _simulateCameraAndOcr() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.camera);
    
    if (pickedFile == null) return;

    setState(() => _isOcrProcessing = true);
    
    try {
      final repo = ref.read(expenseRepositoryProvider);
      final ocrResult = await repo.processReceiptOcr(File(pickedFile.path));
      
      setState(() {
        _isOcrProcessing = false;
        _vendorController.text = ocrResult['vendor'] ?? '';
        _gstController.text = ocrResult['gst_number'] ?? '';
        _amountController.text = (ocrResult['amount'] ?? '').toString();
        
        // Auto-select category if matching
        String suggestedCategory = ocrResult['category'] ?? 'FUEL';
        if (['FUEL', 'TOLL', 'PARKING', 'REPAIR', 'FOOD'].contains(suggestedCategory)) {
          _category = suggestedCategory;
        }
      });

      if (mounted) {
        final risk = (ocrResult['fraud_risk_score'] * 100).toStringAsFixed(0);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('AI OCR Extracted: ${ocrResult['vendor']}, ₹${ocrResult['amount']}. Fraud Risk: $risk%')),
        );
      }
    } catch (e) {
      setState(() => _isOcrProcessing = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('OCR Failed: $e')),
        );
      }
    }
  }

  void _submitExpense() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isSubmitting = true);
    
    try {
      final repo = ref.read(expenseRepositoryProvider);
      final driverId = await SecureStorage.getDriverId() ?? 1;
      
      await repo.createExpense(
        category: _category,
        amount: double.tryParse(_amountController.text) ?? 0,
        description: '${_vendorController.text} (GST: ${_gstController.text})',
        driverId: driverId,
      );
      
      setState(() => _isSubmitting = false);

      if (mounted) {
        ref.invalidate(driverExpensesProvider);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Expense submitted successfully for fleet review!')),
        );
        context.pop();
      }
    } catch (e) {
      setState(() => _isSubmitting = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to submit expense: $e')),
        );
      }
    }
  }

  @override
  void dispose() {
    _amountController.dispose();
    _vendorController.dispose();
    _gstController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Add New Expense')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // AI Camera OCR Scanner Card
              Card(
                color: Theme.of(context).colorScheme.primaryContainer.withOpacity(0.4),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    children: [
                      const Icon(Icons.auto_awesome, size: 40, color: Colors.blue),
                      const SizedBox(height: 8),
                      const Text('Scan Receipt with AI OCR', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      const Text('Automatically extract vendor, GST, date, amount & detect receipt fraud', textAlign: TextAlign.center, style: TextStyle(fontSize: 12)),
                      const SizedBox(height: 16),
                      ElevatedButton.icon(
                        onPressed: _isOcrProcessing ? null : _simulateCameraAndOcr,
                        icon: const Icon(Icons.camera_alt),
                        label: Text(_isOcrProcessing ? 'Processing OCR...' : 'Capture & Scan Receipt'),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              DropdownButtonFormField<String>(
                value: _category,
                decoration: const InputDecoration(labelText: 'Expense Category', prefixIcon: Icon(Icons.category)),
                items: const [
                  DropdownMenuItem(value: 'FUEL', child: Text('Fuel')),
                  DropdownMenuItem(value: 'TOLL', child: Text('Toll')),
                  DropdownMenuItem(value: 'PARKING', child: Text('Parking')),
                  DropdownMenuItem(value: 'REPAIR', child: Text('Repair / Maintenance')),
                  DropdownMenuItem(value: 'FOOD', child: Text('Food / Allowance')),
                ],
                onChanged: (v) => setState(() => _category = v!),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _amountController,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: 'Amount (₹)', prefixIcon: Icon(Icons.currency_rupee)),
                validator: Validators.amount,
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _vendorController,
                decoration: const InputDecoration(labelText: 'Vendor Name', prefixIcon: Icon(Icons.store)),
                validator: (v) => Validators.required(v, 'Vendor name'),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _gstController,
                decoration: const InputDecoration(labelText: 'GST Number (Optional)', prefixIcon: Icon(Icons.receipt_long)),
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isSubmitting ? null : _submitExpense,
                  child: _isSubmitting ? const CircularProgressIndicator() : const Text('Submit Expense'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
