import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:provider/provider.dart';
import 'package:location/location.dart';
import 'package:sensors_plus/sensors_plus.dart';
import 'package:network_info_plus/network_info_plus.dart';
import 'package:screen_brightness/screen_brightness.dart';
import 'package:shared_preferences/shared_preferences.dart';

// Set your backend URL here
const String backendUrl = "http://localhost:5000"; // Local testing
// const String backendUrl = "https://rk-vx3e.onrender.com"; // Hosted on Render

void main() {
  runApp(const SurakshaApp());
}

class SurakshaApp extends StatelessWidget {
  const SurakshaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
      ],
      child: MaterialApp(
        title: 'Canara Bank Suraksha',
        theme: ThemeData(
          primaryColor: Color(0xFF003366),
          colorScheme: ColorScheme.fromSeed(
            seedColor: Color(0xFF003366),
            primary: Color(0xFF003366),
            secondary: Color(0xFFFFD700),
          ),
          scaffoldBackgroundColor: Color(0xFFF5F6FA),
          appBarTheme: AppBarTheme(
            backgroundColor: Color(0xFF003366),
            foregroundColor: Colors.white,
          ),
        ),
        home: const AuthGate(),
      ),
    );
  }
}

class AuthGate extends StatelessWidget {
  const AuthGate({super.key});
  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    if (auth.isLoggedIn) {
      return SessionDataScreen();
    } else {
      return LoginScreen();
    }
  }
}

class AuthProvider extends ChangeNotifier {
  bool isLoggedIn = false;
  String username = "";
  int sessionColumn = 0;
  
  void login(String user, int column) {
    isLoggedIn = true;
    username = user;
    sessionColumn = column;
    notifyListeners();
  }
  
  void logout() {
    isLoggedIn = false;
    username = "";
    sessionColumn = 0;
    notifyListeners();
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  String username = "";
  String password = "";
  String error = "";
  bool loading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Canara Bank Suraksha Login')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              TextFormField(
                decoration: const InputDecoration(labelText: 'Username'),
                onChanged: (v) => username = v,
                validator: (v) => v == null || v.isEmpty ? 'Enter username' : null,
              ),
              TextFormField(
                decoration: const InputDecoration(labelText: 'Password'),
                obscureText: true,
                onChanged: (v) => password = v,
                validator: (v) => v == null || v.isEmpty ? 'Enter password' : null,
              ),
              const SizedBox(height: 16),
              if (error.isNotEmpty) Text(error, style: TextStyle(color: Colors.red)),
              ElevatedButton(
                onPressed: loading ? null : () async {
                  if (_formKey.currentState!.validate()) {
                    setState(() { loading = true; error = ""; });
                    final res = await http.post(
                      Uri.parse('$backendUrl/login'),
                      headers: {'Content-Type': 'application/json'},
                      body: jsonEncode({'username': username, 'password': password}),
                    );
                    if (res.statusCode == 200) {
                      final responseData = jsonDecode(res.body);
                      final sessionColumn = responseData['session_column'] ?? 1;
                      Provider.of<AuthProvider>(context, listen: false).login(username, sessionColumn);
                    } else {
                      setState(() { error = 'Invalid credentials'; });
                    }
                    setState(() { loading = false; });
                  }
                },
                child: loading ? CircularProgressIndicator() : Text('Login'),
              ),
              TextButton(
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => RegisterScreen()),
                  );
                },
                child: Text('Register'),
              ),
              TextButton(
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(builder: (_) => ForgotPasswordScreen()),
                  );
                },
                child: Text('Forgot Password?'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class RegisterScreen extends StatefulWidget {
  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  String username = "";
  String password = "";
  String error = "";
  bool loading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Register')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              TextFormField(
                decoration: const InputDecoration(labelText: 'Username'),
                onChanged: (v) => username = v,
                validator: (v) => v == null || v.isEmpty ? 'Enter username' : null,
              ),
              TextFormField(
                decoration: const InputDecoration(labelText: 'Password'),
                obscureText: true,
                onChanged: (v) => password = v,
                validator: (v) => v == null || v.isEmpty ? 'Enter password' : null,
              ),
              const SizedBox(height: 16),
              if (error.isNotEmpty) Text(error, style: TextStyle(color: Colors.red)),
              ElevatedButton(
                onPressed: loading ? null : () async {
                  if (_formKey.currentState!.validate()) {
                    setState(() { loading = true; error = ""; });
                    final res = await http.post(
                      Uri.parse('$backendUrl/register'),
                      headers: {'Content-Type': 'application/json'},
                      body: jsonEncode({'username': username, 'password': password}),
                    );
                    if (res.statusCode == 200) {
                      Navigator.of(context).pop();
                    } else {
                      setState(() { error = 'Registration failed'; });
                    }
                    setState(() { loading = false; });
                  }
                },
                child: loading ? CircularProgressIndicator() : Text('Register'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class ForgotPasswordScreen extends StatefulWidget {
  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  String username = "";
  String newPassword = "";
  String error = "";
  bool loading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Forgot Password')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              TextFormField(
                decoration: const InputDecoration(labelText: 'Username'),
                onChanged: (v) => username = v,
                validator: (v) => v == null || v.isEmpty ? 'Enter username' : null,
              ),
              TextFormField(
                decoration: const InputDecoration(labelText: 'New Password'),
                obscureText: true,
                onChanged: (v) => newPassword = v,
                validator: (v) => v == null || v.isEmpty ? 'Enter new password' : null,
              ),
              const SizedBox(height: 16),
              if (error.isNotEmpty) Text(error, style: TextStyle(color: Colors.red)),
              ElevatedButton(
                onPressed: loading ? null : () async {
                  if (_formKey.currentState!.validate()) {
                    setState(() { loading = true; error = ""; });
                    final res = await http.post(
                      Uri.parse('$backendUrl/forgot_password'),
                      headers: {'Content-Type': 'application/json'},
                      body: jsonEncode({'username': username, 'new_password': newPassword}),
                    );
                    if (res.statusCode == 200) {
                      Navigator.of(context).pop();
                    } else {
                      setState(() { error = 'Reset failed'; });
                    }
                    setState(() { loading = false; });
                  }
                },
                child: loading ? CircularProgressIndicator() : Text('Reset Password'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class SessionDataScreen extends StatefulWidget {
  @override
  State<SessionDataScreen> createState() => _SessionDataScreenState();
}

class _SessionDataScreenState extends State<SessionDataScreen> {
  bool consent = true; // Default to true
  String status = "";
  bool loading = false;
  String sessionStart = "";
  String sessionEnd = "";
  List<Offset> swipeCoordinates = [];
  String swipePattern = "";
  String gyroscopePattern = "";
  String wifiSsid = "";
  String wifiBssid = "";
  double locationLat = 0.0;
  double locationLon = 0.0;
  String loginTime = "";
  double screenBrightness = 0.0;
  bool isGestureActive = false;

  @override
  void initState() {
    super.initState();
    _initSession();
  }

  Future<void> _initSession() async {
    sessionStart = DateTime.now().toIso8601String();
    loginTime = sessionStart;
    
    // Get WiFi info
    try {
      final info = NetworkInfo();
      wifiSsid = (await info.getWifiName()) ?? "";
      wifiBssid = (await info.getWifiBSSID()) ?? "";
    } catch (e) {
      print('WiFi info error: $e');
      wifiSsid = "";
      wifiBssid = "";
    }
    
    // Get location
    try {
      final loc = Location();
      final locData = await loc.getLocation();
      locationLat = locData.latitude ?? 0.0;
      locationLon = locData.longitude ?? 0.0;
    } catch (e) {
      print('Location error: $e');
      locationLat = 0.0;
      locationLon = 0.0;
    }
    
    // Get brightness
    try {
      screenBrightness = await ScreenBrightness().current ?? 0.0;
    } catch (e) {
      print('Brightness error: $e');
      screenBrightness = 0.0;
    }
    
    // Listen to gyroscope
    try {
      gyroscopeEvents.listen((GyroscopeEvent event) {
        setState(() {
          gyroscopePattern = "${event.x.toStringAsFixed(3)},${event.y.toStringAsFixed(3)},${event.z.toStringAsFixed(3)}";
        });
      });
    } catch (e) {
      print('Gyroscope error: $e');
      gyroscopePattern = "";
    }
    
    setState(() {});
  }

  void _onPanStart(DragStartDetails details) {
    setState(() {
      isGestureActive = true;
      swipeCoordinates.clear();
      swipeCoordinates.add(details.globalPosition);
    });
  }

  void _onPanUpdate(DragUpdateDetails details) {
    if (isGestureActive) {
      setState(() {
        swipeCoordinates.add(details.globalPosition);
      });
    }
  }

  void _onPanEnd(DragEndDetails details) {
    setState(() {
      isGestureActive = false;
      if (swipeCoordinates.length > 1) {
        // Analyze swipe pattern
        swipePattern = _analyzeSwipePattern(swipeCoordinates);
      }
    });
  }

  String _analyzeSwipePattern(List<Offset> coordinates) {
    if (coordinates.length < 2) return "insufficient_data";
    
    // Calculate direction and distance
    Offset start = coordinates.first;
    Offset end = coordinates.last;
    
    double deltaX = end.dx - start.dx;
    double deltaY = end.dy - start.dy;
    double distance = (end - start).distance;
    
    // Determine primary direction
    String direction = "";
    if (distance < 50) {
      direction = "tap";
    } else if (deltaX.abs() > deltaY.abs()) {
      direction = deltaX > 0 ? "right" : "left";
    } else {
      direction = deltaY > 0 ? "down" : "up";
    }
    
    // Calculate complexity (number of direction changes)
    int directionChanges = 0;
    for (int i = 1; i < coordinates.length - 1; i++) {
      Offset prev = coordinates[i - 1];
      Offset curr = coordinates[i];
      Offset next = coordinates[i + 1];
      
      double angle1 = (curr - prev).direction;
      double angle2 = (next - curr).direction;
      
      if ((angle1 - angle2).abs() > 0.5) {
        directionChanges++;
      }
    }
    
    return "${direction}_${directionChanges}_${distance.toStringAsFixed(0)}";
  }

  Future<void> _submitSession() async {
    setState(() { loading = true; status = ""; });
    sessionEnd = DateTime.now().toIso8601String();
    
    final username = Provider.of<AuthProvider>(context, listen: false).username;
    
    // Convert coordinates to string format
    String coordinatesString = swipeCoordinates.map((offset) => 
      "${offset.dx.toStringAsFixed(2)},${offset.dy.toStringAsFixed(2)}"
    ).join("|");
    
    // Prepare data with proper null handling
    Map<String, dynamic> sessionData = {
      'username': username,
      'session_start': sessionStart,
      'session_end': sessionEnd,
      'swipe_gesture_coordinates': coordinatesString.isEmpty ? null : coordinatesString,
      'swipe_gesture_pattern': swipePattern.isEmpty ? null : swipePattern,
      'gyroscope_pattern': gyroscopePattern.isEmpty ? null : gyroscopePattern,
      'wifi_ssid': wifiSsid.isEmpty ? null : wifiSsid,
      'wifi_bssid': wifiBssid.isEmpty ? null : wifiBssid,
      'location_lat': locationLat,
      'location_lon': locationLon,
      'login_time': loginTime,
      'screen_brightness': screenBrightness,
      'consent': consent,
    };
    
    print('Submitting session data: $sessionData');
    
    final res = await http.post(
      Uri.parse('$backendUrl/collect_data'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(sessionData),
    );
    
    if (res.statusCode == 200) {
      final responseData = jsonDecode(res.body);
      setState(() { 
        status = "✅ Session data submitted successfully! Session ID: ${responseData['session_id']}"; 
      });
    } else {
      try {
        final errorData = jsonDecode(res.body);
        setState(() { 
          status = "❌ Submission failed: ${errorData['error'] ?? 'Unknown error'}"; 
        });
      } catch (e) {
        setState(() { 
          status = "❌ Submission failed: ${res.statusCode} - ${res.body}"; 
        });
      }
    }
    setState(() { loading = false; });
  }

  @override
  Widget build(BuildContext context) {
    final auth = Provider.of<AuthProvider>(context);
    return Scaffold(
      appBar: AppBar(
        title: Text('Session Data - Column ${auth.sessionColumn}'),
        actions: [
          IconButton(
            icon: Icon(Icons.logout),
            onPressed: () {
              auth.logout();
            },
          ),
          IconButton(
            icon: Icon(Icons.download),
            onPressed: () async {
              try {
                final response = await http.get(Uri.parse('$backendUrl/export_excel'));
                if (response.statusCode == 200) {
                  setState(() {
                    status = "Excel file downloaded successfully!";
                  });
                } else {
                  setState(() {
                    status = "Download failed: ${response.body}";
                  });
                }
              } catch (e) {
                setState(() {
                  status = "Download error: $e";
                });
              }
            },
            tooltip: 'Download Excel',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Welcome, ${auth.username}', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            Text('Session Column: ${auth.sessionColumn}', style: TextStyle(fontSize: 14, color: Colors.grey)),
            SizedBox(height: 20),
            
            // Gesture Detection Area
            Container(
              height: 180,
              decoration: BoxDecoration(
                border: Border.all(color: isGestureActive ? Colors.blue : Colors.grey),
                borderRadius: BorderRadius.circular(8),
                color: isGestureActive ? Colors.blue.withOpacity(0.1) : Colors.grey.withOpacity(0.1),
              ),
              child: GestureDetector(
                onPanStart: _onPanStart,
                onPanUpdate: _onPanUpdate,
                onPanEnd: _onPanEnd,
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        isGestureActive ? Icons.touch_app : Icons.gesture,
                        size: 40,
                        color: isGestureActive ? Colors.blue : Colors.grey,
                      ),
                      SizedBox(height: 8),
                      Text(
                        isGestureActive ? 'Recording Gesture...' : 'Swipe here to record gesture',
                        style: TextStyle(
                          color: isGestureActive ? Colors.blue : Colors.grey,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      if (swipePattern.isNotEmpty)
                        Padding(
                          padding: EdgeInsets.only(top: 8),
                          child: Text(
                            'Pattern: $swipePattern',
                            style: TextStyle(fontSize: 11, color: Colors.green),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
            
            SizedBox(height: 16),
            
            // Data Display
            Card(
              child: Padding(
                padding: EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Session Data', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                    SizedBox(height: 8),
                    Text('Coordinates: ${swipeCoordinates.length} points', style: TextStyle(fontSize: 13)),
                    Text('Pattern: ${swipePattern.isEmpty ? "None" : swipePattern}', style: TextStyle(fontSize: 13)),
                    Text('Gyroscope: ${gyroscopePattern.isEmpty ? "None" : gyroscopePattern}', style: TextStyle(fontSize: 13)),
                    Text('WiFi: ${wifiSsid.isEmpty ? "None" : wifiSsid}', style: TextStyle(fontSize: 13)),
                    Text('Location: ${locationLat.toStringAsFixed(4)}, ${locationLon.toStringAsFixed(4)}', style: TextStyle(fontSize: 13)),
                    Text('Brightness: ${screenBrightness.toStringAsFixed(2)}', style: TextStyle(fontSize: 13)),
                  ],
                ),
              ),
            ),
            
            SizedBox(height: 16),
            
            SwitchListTile(
              title: Text('Data Collection Consent', style: TextStyle(fontSize: 14)),
              subtitle: Text('You can disable data collection if needed', style: TextStyle(fontSize: 12)),
              value: consent,
              onChanged: (v) => setState(() => consent = v),
              contentPadding: EdgeInsets.symmetric(horizontal: 8),
            ),
            
            SizedBox(height: 16),
            
            ElevatedButton(
              onPressed: loading ? null : _submitSession,
              style: ElevatedButton.styleFrom(
                minimumSize: Size(double.infinity, 45),
              ),
              child: loading ? CircularProgressIndicator() : Text('Submit Session Data'),
            ),
            
            SizedBox(height: 12),
            
            if (status.isNotEmpty) 
              Container(
                padding: EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: status.contains('success') ? Colors.green.withOpacity(0.1) : Colors.red.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  status,
                  style: TextStyle(
                    color: status.contains('success') ? Colors.green : Colors.red,
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                  ),
                ),
              ),
            
            SizedBox(height: 20), // Extra padding at bottom
          ],
        ),
      ),
    );
  }
}
