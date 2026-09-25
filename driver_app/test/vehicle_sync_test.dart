import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:driver_app/features/dashboard/presentation/providers/dashboard_providers.dart';
import 'package:driver_app/features/auth/data/auth_repository.dart';

// Mock repository
class MockAuthRepository extends AuthRepository {
  MockAuthRepository(super.apiClient);

  String? _currentVehicle = 'Vehicle A';

  void adminSetsVehicle(String? vehicle) {
    _currentVehicle = vehicle;
  }

  @override
  Future<Map<String, dynamic>> getAssignedVehicle() async {
    if (_currentVehicle == null) {
      throw Exception('No vehicle allocated');
    }
    return {
      'registration_number': _currentVehicle,
      'make': 'TestMake',
      'model': 'TestModel'
    };
  }
}

void main() {
  test('Vehicle Synchronization on Resume', () async {
    // Note: We use a simulated container rather than spinning up the entire flutter app
    // because physical device test is not available in the current environment.
    
    final mockRepo = MockAuthRepository(null as dynamic); // bypass api client for test
    
    final container = ProviderContainer(
      overrides: [
        authRepositoryProvider.overrideWithValue(mockRepo),
      ],
    );

    // 1. App starts, gets Vehicle A
    final firstFetch = await container.read(assignedVehicleProvider.future);
    expect(firstFetch['registration_number'], 'Vehicle A');

    // 2. Admin assigns Vehicle B in the backend
    mockRepo.adminSetsVehicle('Vehicle B');

    // 3. App Resumes -> Invalidate Provider
    container.invalidate(assignedVehicleProvider);
    
    // 4. App UI rebuilds and watches provider again
    final secondFetch = await container.read(assignedVehicleProvider.future);
    expect(secondFetch['registration_number'], 'Vehicle B');
    
    // 5. Admin removes vehicle
    mockRepo.adminSetsVehicle(null);
    
    // 6. App Resumes -> Invalidate Provider
    container.invalidate(assignedVehicleProvider);
    
    // 7. App tries to fetch, gets empty/error state
    expect(
      () async => await container.read(assignedVehicleProvider.future),
      throwsException,
    );
  });
}
