import 'package:intl/intl.dart';

class Formatters {
  static String formatCurrency(dynamic amount) {
    if (amount == null) return 'N/A';
    double val = 0.0;
    if (amount is int) val = amount.toDouble();
    if (amount is double) val = amount;
    if (amount is String) val = double.tryParse(amount) ?? 0.0;
    
    final formatter = NumberFormat.currency(locale: 'en_IN', symbol: '₹', decimalDigits: 0);
    return formatter.format(val);
  }

  static String formatDate(String? isoString) {
    if (isoString == null || isoString.isEmpty) return 'Not available';
    try {
      final dateTime = DateTime.parse(isoString).toLocal();
      return DateFormat("dd MMM yyyy, h:mm a").format(dateTime); // e.g. 26 Aug 2026, 8:36 PM
    } catch (e) {
      return isoString;
    }
  }
}
