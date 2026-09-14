// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Hindi (`hi`).
class AppLocalizationsHi extends AppLocalizations {
  AppLocalizationsHi([String locale = 'hi']) : super(locale);

  @override
  String get appTitle => 'फ्लीटगार्ड (FleetGuard)';

  @override
  String get home => 'होम';

  @override
  String get fleet => 'फ्लीट';

  @override
  String get trips => 'यात्राएं';

  @override
  String get finance => 'वित्त';

  @override
  String get more => 'अधिक';

  @override
  String get copilot => 'कोपायलट';

  @override
  String get settings => 'सेटिंग्स';

  @override
  String get profile => 'प्रोफ़ाइल';

  @override
  String get language => 'भाषा';

  @override
  String get theme => 'थीम';

  @override
  String get light => 'लाइट';

  @override
  String get dark => 'डार्क';

  @override
  String get system => 'सिस्टम';

  @override
  String get logout => 'लॉग आउट';

  @override
  String get notifications => 'सूचनाएं';

  @override
  String get noNotifications => 'अभी तक कोई सूचना नहीं';

  @override
  String get activeVehicles => 'सक्रिय वाहन';

  @override
  String get noActiveVehicles => 'कोई सक्रिय वाहन नहीं';

  @override
  String get noMapConfig => 'मैप कॉन्फ़िगरेशन गायब है';

  @override
  String get routeMapUnavailable => 'रूट मैप उपलब्ध नहीं है';

  @override
  String get pleaseConfigGeoapify =>
      'कृपया जियोएपीफाई एपीआई कुंजी कॉन्फ़िगर करें।';

  @override
  String get noLocationData => 'इस यात्रा के लिए स्थान डेटा उपलब्ध नहीं है।';

  @override
  String get noExpensesFound => 'कोई खर्च नहीं मिला';

  @override
  String get noExpensesRecorded => 'इस अवधि में कोई खर्च दर्ज नहीं किया गया।';

  @override
  String get noPayments => 'कोई भुगतान नहीं';

  @override
  String get noDriverPayments =>
      'इस अवधि के लिए कोई ड्राइवर भुगतान या अग्रिम नहीं मिला।';

  @override
  String get truckAddedSuccess => 'ट्रक सफलतापूर्वक जोड़ा गया';

  @override
  String get regNumberRequired => 'पंजीकरण संख्या आवश्यक है';

  @override
  String get manufacturerRequired => 'निर्माता आवश्यक है';

  @override
  String get failedLoadKPIs => 'केपीआई लोड करने में विफल';

  @override
  String get failedLoadExpenses => 'खर्च लोड करने में विफल।';
}
