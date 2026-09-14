// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'FleetGuard';

  @override
  String get home => 'Home';

  @override
  String get fleet => 'Fleet';

  @override
  String get trips => 'Trips';

  @override
  String get finance => 'Finance';

  @override
  String get more => 'More';

  @override
  String get copilot => 'Copilot';

  @override
  String get settings => 'Settings';

  @override
  String get profile => 'Profile';

  @override
  String get language => 'Language';

  @override
  String get theme => 'Theme';

  @override
  String get light => 'Light';

  @override
  String get dark => 'Dark';

  @override
  String get system => 'System';

  @override
  String get logout => 'Logout';

  @override
  String get notifications => 'Notifications';

  @override
  String get noNotifications => 'No notifications yet';

  @override
  String get activeVehicles => 'Active Vehicles';

  @override
  String get noActiveVehicles => 'No active vehicles';

  @override
  String get noMapConfig => 'Map configuration missing';

  @override
  String get routeMapUnavailable => 'Route Map Unavailable';

  @override
  String get pleaseConfigGeoapify => 'Please configure Geoapify API key.';

  @override
  String get noLocationData => 'Location data is not available for this trip.';

  @override
  String get noExpensesFound => 'No Expenses Found';

  @override
  String get noExpensesRecorded => 'No expenses recorded in this period.';

  @override
  String get noPayments => 'No Payments';

  @override
  String get noDriverPayments =>
      'No driver payments or advances found for this period.';

  @override
  String get truckAddedSuccess => 'Truck added successfully';

  @override
  String get regNumberRequired => 'Registration number is required';

  @override
  String get manufacturerRequired => 'Manufacturer is required';

  @override
  String get failedLoadKPIs => 'Failed to load KPIs.';

  @override
  String get failedLoadExpenses => 'Failed to load expenses.';
}
