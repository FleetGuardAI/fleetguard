/// All API endpoint constants — single source of truth
class ApiEndpoints {
  ApiEndpoints._();

  // --- Driver App Auth ---
  static const String verifyInvite = '/api/v1/driver-app/verify-invite';
  static const String sendOtp = '/api/v1/driver-app/send-otp';
  static const String verifyOtp = '/api/v1/driver-app/verify-otp';
  static const String driverRegister = '/api/v1/driver-app/register';
  static const String uploadDocument = '/api/v1/driver-app/upload-document';
  static const String faceVerify = '/api/v1/driver-app/face-verify';
  static const String driverProfile = '/api/v1/driver-app/profile';
  static const String updateFcmToken = '/api/v1/driver-app/fcm-token';

  // --- Duty Management ---
  static const String dutyStart = '/api/v1/driver-app/duty/start';
  static const String dutyEnd = '/api/v1/driver-app/duty/end';
  static const String dutyBreak = '/api/v1/driver-app/duty/break';
  static const String dutyResume = '/api/v1/driver-app/duty/resume';

  // --- Trips ---
  static const String todayTrips = '/api/v1/driver-app/trips/today';
  static String tripStart(int id) => '/api/v1/driver-app/trips/$id/start';
  static String tripPause(int id) => '/api/v1/driver-app/trips/$id/pause';
  static String tripResume(int id) => '/api/v1/driver-app/trips/$id/resume';
  static String tripComplete(int id) => '/api/v1/driver-app/trips/$id/complete';
  static String tripStartSelfie(int id) => '/api/v1/driver-app/trips/$id/start-selfie';

  // --- Vehicle ---
  static const String assignedVehicle = '/api/v1/driver-app/vehicle';

  // --- Location ---
  static const String locationBatch = '/api/v1/driver-app/location/batch';

  // --- Expenses ---
  static const String driverExpenses = '/api/v1/driver-app/expenses';
  static const String expenseOcr = '/api/v1/driver-app/expenses/ocr';

  // --- Inspections ---
  static const String driverInspections = '/api/v1/driver-app/inspections';

  // --- POD ---
  static String pod(int tripId) => '/api/v1/driver-app/pod/$tripId';

  // --- Emergency ---
  static const String sos = '/api/v1/driver-app/sos';
  static const String activeSos = '/api/v1/driver-app/sos/active';

  // --- Wallet ---
  static const String wallet = '/api/v1/driver-app/wallet';
  static const String advanceRequest = '/api/v1/driver-app/wallet/advance-request';

  // --- Documents ---
  static const String driverDocuments = '/api/v1/driver-app/documents';

  // --- Notifications ---
  static const String notifications = '/api/v1/driver-app/notifications';

  // --- WebSocket ---
  static String driverWs(int driverId) => '/api/v1/ws/driver/$driverId';
}
