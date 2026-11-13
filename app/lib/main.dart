import 'package:material_ui/material_ui.dart';
import 'package:geolocator/geolocator.dart';
import 'package:kakao_map_sdk/kakao_map_sdk.dart';

import 'api.dart' as api;
import 'screens.dart';

/// 카카오 네이티브 앱 키. 실행: flutter run --dart-define-from-file=.env
const kakaoKey = String.fromEnvironment('KAKAO_NATIVE_APP_KEY');
const cuisineList = ['치킨', '피자', '족발보쌈', '중식', '마라탕'];

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // 키가 없으면 지도 없이 목록으로 미리보기 (카카오 SDK는 x86 에뮬레이터에서 동작하지 않음)
  if (kakaoKey.isNotEmpty) await KakaoMapSdk.instance.initialize(kakaoKey);
  runApp(MaterialApp(
    title: '위생지도',
    theme: ThemeData(colorSchemeSeed: Colors.green, useMaterial3: true),
    home: const MapScreen(),
  ));
}

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  static const haeundae = LatLng(35.1631, 129.1586); // 위치 권한이 없을 때 기본 위치

  KakaoMapController? _map;
  Map<api.PinType, PoiStyle>? _styles;
  final _pois = <Poi>[];
  LatLng _center = haeundae;
  String? _cuisine = '치킨';
  String? _error;
  int? _count;
  bool _loading = false, _again = false;
  List<api.Shop> _shops = [];

  @override
  void initState() {
    super.initState();
    if (kakaoKey.isEmpty) _load(); // 지도가 없으면 onMapReady가 안 불리므로 바로 불러온다
  }

  Future<void> _onReady(KakaoMapController c) async {
    _map = c;
    _styles = {
      for (final t in api.PinType.values)
        t: PoiStyle(icon: await KImage.fromWidget(PinIcon(t), const Size(40, 40)))
    };
    await _load();
    await _moveToMyLocation(); // 이동이 끝나면 onCameraMoveEnd가 다시 불러온다
  }

  Future<void> _moveToMyLocation() async {
    try {
      var perm = await Geolocator.checkPermission();
      if (perm == LocationPermission.denied) perm = await Geolocator.requestPermission();
      if (perm == LocationPermission.denied || perm == LocationPermission.deniedForever) return;
      final p = await Geolocator.getCurrentPosition();
      await _map?.moveCamera(CameraUpdate.newCenterPosition(LatLng(p.latitude, p.longitude)));
    } catch (_) {} // 위치를 못 얻으면 기본 위치 그대로
  }

  /// 겹쳐 불리면 끝난 뒤 한 번 더 돈다 (핀 목록을 동시에 고치지 않도록)
  Future<void> _load() async {
    if (_loading) {
      _again = true;
      return;
    }
    _loading = true;
    try {
      do {
        _again = false;
        await _loadOnce();
      } while (_again);
    } finally {
      _loading = false;
    }
  }

  Future<void> _loadOnce() async {
    final map = _map, styles = _styles;
    if (kakaoKey.isNotEmpty && (map == null || styles == null)) return;
    try {
      final shops = await api.nearby(_center.latitude, _center.longitude, cuisine: _cuisine);
      if (map != null && styles != null) {
        for (final p in _pois) {
          await map.labelLayer.removePoi(p);
        }
        _pois.clear();
        for (final s in shops) {
          _pois.add(await map.labelLayer.addPoi(LatLng(s.lat!, s.lng!),
              style: styles[s.pin]!, onClick: () => _open(s.id)));
        }
      }
      if (mounted) {
        setState(() {
          _shops = shops;
          _count = shops.length;
          _error = null;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _error = '서버에 연결할 수 없습니다');
    }
  }

  void _open(String id) =>
      Navigator.push(context, MaterialPageRoute(builder: (_) => DetailScreen(id: id)));

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('위생지도'),
        actions: [
          IconButton(
            icon: const Icon(Icons.search),
            tooltip: '가게 검색',
            onPressed: () => Navigator.push(
                context, MaterialPageRoute(builder: (_) => SearchScreen(onOpen: _open))),
          ),
        ],
      ),
      body: Stack(children: [
        if (kakaoKey.isEmpty)
          ListView(padding: const EdgeInsets.only(top: 56, bottom: 80), children: [
            for (final s in _shops) ShopTile(s, onTap: () => _open(s.id)),
          ])
        else
          KakaoMap(
            option: const KakaoMapOption(position: haeundae, zoomLevel: 15),
            onMapReady: _onReady,
            onCameraMoveEnd: (pos, _) {
              _center = pos.position;
              _load();
            },
          ),
        Positioned(
          top: 8,
          left: 8,
          right: 8,
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(children: [
              for (final c in cuisineList)
                Padding(
                  padding: const EdgeInsets.only(right: 6),
                  child: FilterChip(
                    label: Text(c),
                    selected: _cuisine == c,
                    onSelected: (on) {
                      setState(() => _cuisine = on ? c : null);
                      _load();
                    },
                  ),
                ),
            ]),
          ),
        ),
        Positioned(
          bottom: 16,
          left: 16,
          right: 16,
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Text(
                _error ?? (_count == null ? '불러오는 중…' : '주변 2km · ${_cuisine ?? '전체'} $_count곳'),
                textAlign: TextAlign.center,
              ),
            ),
          ),
        ),
      ]),
    );
  }
}
