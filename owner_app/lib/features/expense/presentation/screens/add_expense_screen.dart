import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import '../../../../core/theme/app_colors.dart';
import '../providers/expense_provider.dart';
import '../../data/expense_repository.dart';
import '../../../../features/fleet/presentation/providers/fleet_provider.dart';
import '../../../../features/trip/presentation/providers/trip_provider.dart';

class AddExpenseScreen extends ConsumerStatefulWidget {
  const AddExpenseScreen({super.key});

  @override
  ConsumerState<AddExpenseScreen> createState() => _AddExpenseScreenState();
}

class _AddExpenseScreenState extends ConsumerState<AddExpenseScreen> {
  final _formKey = GlobalKey<FormState>();
  final _amountController = TextEditingController();
  final _vendorController = TextEditingController();
  final _dateController = TextEditingController();
  final _descriptionController = TextEditingController();
  
  String? _selectedCategory;
  int? _selectedVehicleId;
  int? _selectedTripId;
  String? _receiptUrl;
  bool _isProcessingOCR = false;
  bool _isSubmitting = false;

  final List<String> _categories = [
    'FUEL', 'TOLL', 'MAINTENANCE', 'PARKING', 'FOOD', 'REPAIR', 'MISCELLANEOUS'
  ];

  @override
  void initState() {
    super.initState();
    _dateController.text = DateFormat('yyyy-MM-dd').format(DateTime.now());
  }

  @override
  void dispose() {
    _amountController.dispose();
    _vendorController.dispose();
    _dateController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  Future<void> _pickAndProcessImage(ImageSource source) async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: source);

    if (pickedFile != null) {
      setState(() {
        _isProcessingOCR = true;
      });

      try {
        final repo = ref.read(fleetExpenseRepositoryProvider);
        final ocrResult = await repo.uploadReceiptForOCR(pickedFile.path);
        
        if (mounted) {
          setState(() {
            _amountController.text = ocrResult['amount']?.toString() ?? '';
            _vendorController.text = ocrResult['vendor'] ?? '';
            _dateController.text = ocrResult['date'] ?? _dateController.text;
            if (ocrResult['category'] != null && _categories.contains(ocrResult['category'].toString().toUpperCase())) {
              _selectedCategory = ocrResult['category'].toString().toUpperCase();
            }
            _receiptUrl = pickedFile.path;
          });
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('OCR extraction successful')),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Failed to process receipt: $e'), backgroundColor: AppColors.error),
          );
        }
      } finally {
        if (mounted) {
          setState(() {
            _isProcessingOCR = false;
          });
        }
      }
    }
  }

  Future<void> _submitExpense() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isSubmitting = true;
    });

    try {
      final repo = ref.read(fleetExpenseRepositoryProvider);
      final payload = {
        'amount': double.tryParse(_amountController.text) ?? 0.0,
        'category': _selectedCategory ?? 'MISCELLANEOUS',
        'description': _descriptionController.text.isNotEmpty ? _descriptionController.text : _vendorController.text,
        'vehicle_id': _selectedVehicleId,
        'trip_id': _selectedTripId,
      };

      await repo.createExpense(payload);
      
      ref.invalidate(fleetExpensesProvider);
      
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Expense added successfully'), backgroundColor: AppColors.statusGreen),
        );
        Navigator.pop(context);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to submit expense: $e'), backgroundColor: AppColors.error),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isSubmitting = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final vehiclesAsync = ref.watch(vehiclesProvider);
    final tripsAsync = ref.watch(fleetTripsProvider);

    return Scaffold(
      backgroundColor: isDark ? AppColors.darkBackground : AppColors.lightBackground,
      appBar: AppBar(
        title: Text('Add Expense', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
        backgroundColor: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
      ),
      body: _isProcessingOCR
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const CircularProgressIndicator(),
                  const SizedBox(height: 16),
                  Text('Processing Receipt (OCR)...', style: TextStyle(color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                ],
              ),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    // Receipt Upload Section
                    Container(
                      padding: const EdgeInsets.all(24),
                      decoration: BoxDecoration(
                        color: isDark ? AppColors.darkCardBackground : AppColors.lightCardBackground,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.primary.withValues(alpha: 0.5), width: 1.5, style: BorderStyle.solid),
                      ),
                      child: Column(
                        children: [
                          Icon(Icons.receipt_long, size: 48, color: AppColors.primary.withValues(alpha: 0.8)),
                          const SizedBox(height: 12),
                          Text('Scan or Upload Receipt', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: isDark ? AppColors.darkOnSurface : AppColors.lightOnSurface)),
                          const SizedBox(height: 16),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              ElevatedButton.icon(
                                onPressed: () => _pickAndProcessImage(ImageSource.camera),
                                icon: const Icon(Icons.camera_alt),
                                label: const Text('Scan'),
                              ),
                              const SizedBox(width: 16),
                              OutlinedButton.icon(
                                onPressed: () => _pickAndProcessImage(ImageSource.gallery),
                                icon: const Icon(Icons.photo_library),
                                label: const Text('Gallery'),
                              ),
                            ],
                          )
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),

                    // Amount
                    TextFormField(
                      controller: _amountController,
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      decoration: InputDecoration(
                        labelText: 'Amount (₹)',
                        prefixIcon: const Icon(Icons.currency_rupee),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      validator: (value) => value == null || value.isEmpty ? 'Required' : null,
                    ),
                    const SizedBox(height: 16),

                    // Category
                    DropdownButtonFormField<String>(
                      value: _selectedCategory,
                      decoration: InputDecoration(
                        labelText: 'Expense Category',
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      items: _categories.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
                      onChanged: (val) => setState(() => _selectedCategory = val),
                      validator: (value) => value == null ? 'Required' : null,
                    ),
                    const SizedBox(height: 16),

                    // Vendor
                    TextFormField(
                      controller: _vendorController,
                      decoration: InputDecoration(
                        labelText: 'Vendor / Merchant',
                        prefixIcon: const Icon(Icons.store),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                    ),
                    const SizedBox(height: 16),
                    
                    // Date
                    TextFormField(
                      controller: _dateController,
                      decoration: InputDecoration(
                        labelText: 'Date (YYYY-MM-DD)',
                        prefixIcon: const Icon(Icons.calendar_today),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Description
                    TextFormField(
                      controller: _descriptionController,
                      decoration: InputDecoration(
                        labelText: 'Description',
                        prefixIcon: const Icon(Icons.description),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                    ),
                    const SizedBox(height: 16),

                    // Vehicle
                    vehiclesAsync.when(
                      data: (vehicles) => DropdownButtonFormField<int>(
                        value: _selectedVehicleId,
                        decoration: InputDecoration(
                          labelText: 'Vehicle (Optional)',
                          prefixIcon: const Icon(Icons.local_shipping),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        items: [
                          const DropdownMenuItem<int>(value: null, child: Text('None')),
                          ...vehicles.map((v) => DropdownMenuItem(
                                value: v.id,
                                child: Text(v.licensePlate),
                              ))
                        ],
                        onChanged: (val) => setState(() => _selectedVehicleId = val),
                      ),
                      loading: () => const LinearProgressIndicator(),
                      error: (_, __) => const Text('Failed to load vehicles'),
                    ),
                    const SizedBox(height: 16),

                    // Trip
                    tripsAsync.when(
                      data: (trips) => DropdownButtonFormField<int>(
                        value: _selectedTripId,
                        decoration: InputDecoration(
                          labelText: 'Trip (Optional)',
                          prefixIcon: const Icon(Icons.route),
                          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        items: [
                          const DropdownMenuItem<int>(value: null, child: Text('None')),
                          ...trips.map((t) => DropdownMenuItem(
                                value: t.id,
                                child: Text('${t.tripId} (${t.originLocation ?? 'Unknown'} → ${t.destinationLocation ?? 'Unknown'})'),
                              ))
                        ],
                        onChanged: (val) => setState(() => _selectedTripId = val),
                      ),
                      loading: () => const LinearProgressIndicator(),
                      error: (_, __) => const Text('Failed to load trips'),
                    ),
                    const SizedBox(height: 32),

                    SizedBox(
                      height: 50,
                      child: ElevatedButton(
                        onPressed: _isSubmitting ? null : _submitExpense,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.primary,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                        child: _isSubmitting 
                          ? const CircularProgressIndicator(color: Colors.white)
                          : const Text('Save Expense', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                      ),
                    ),
                  ],
                ),
              ),
            ),
    );
  }
}
