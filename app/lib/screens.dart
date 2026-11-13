import 'dart:async';

import 'package:material_ui/material_ui.dart';

import 'api.dart' as api;

/// 지도 핀. shortcut: 이모지 임시 캐릭터, 캐릭터 디자인이 정해지면 이미지로 바꾼다
class PinIcon extends StatelessWidget {
  final api.PinType type;
  const PinIcon(this.type, {super.key});

  static (String, Color, String) info(api.PinType t) => switch (t) {
        api.PinType.good => ('😋', Colors.green, '위생등급 지정'),
        api.PinType.warn => ('😷', Colors.orange, '위생 처분 공표 중'),
        api.PinType.plain => ('🍽️', Colors.grey, '위생등급 정보 없음'),
      };

  @override
  Widget build(BuildContext context) {
    final (emoji, color, _) = info(type);
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        shape: BoxShape.circle,
        border: Border.all(color: color, width: 3),
      ),
      alignment: Alignment.center,
      child: Text(emoji, style: const TextStyle(fontSize: 20)),
    );
  }
}

class ShopTile extends StatelessWidget {
  final api.Shop shop;
  final VoidCallback onTap;
  const ShopTile(this.shop, {super.key, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final (_, _, label) = PinIcon.info(shop.pin);
    return ListTile(
      leading: SizedBox(width: 40, height: 40, child: PinIcon(shop.pin)),
      title: Text(shop.name),
      subtitle: Text('$label · ${shop.addr}', maxLines: 1, overflow: TextOverflow.ellipsis),
      onTap: onTap,
    );
  }
}

class SearchScreen extends StatefulWidget {
  final void Function(String id) onOpen;
  const SearchScreen({super.key, required this.onOpen});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  Timer? _debounce;
  List<api.Shop>? _results;
  String? _error;
  String _q = '';

  void _onChanged(String q) {
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 300), () async {
      _q = q.trim();
      if (_q.isEmpty) return setState(() => _results = null);
      try {
        final r = await api.search(_q);
        if (mounted && _q == q.trim()) {
          setState(() {
            _results = r;
            _error = null;
          });
        }
      } catch (_) {
        if (mounted) setState(() => _error = '서버에 연결할 수 없습니다');
      }
    });
  }

  @override
  void dispose() {
    _debounce?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final results = _results;
    return Scaffold(
      appBar: AppBar(
        title: TextField(
          autofocus: true,
          decoration: const InputDecoration(hintText: '가게 이름 (예: 교촌, BBQ)', border: InputBorder.none),
          onChanged: _onChanged,
        ),
      ),
      body: _error != null
          ? Center(child: Text(_error!))
          : results == null
              ? const SizedBox()
              : results.isEmpty
                  ? const Center(child: Text('검색 결과가 없습니다'))
                  : ListView(children: [
                      for (final s in results) ShopTile(s, onTap: () => widget.onOpen(s.id)),
                    ]),
    );
  }
}

class DetailScreen extends StatelessWidget {
  final String id;
  const DetailScreen({super.key, required this.id});

  static const _category = {'hygiene': '위생', 'conduct': '영업질서', 'unknown': '기타'};

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(),
      body: FutureBuilder(
        future: api.detail(id),
        builder: (context, snap) {
          if (snap.hasError) return const Center(child: Text('정보를 불러올 수 없습니다'));
          final d = snap.data;
          if (d == null) return const Center(child: CircularProgressIndicator());
          final shop = api.Shop.fromJson(d);
          final (_, _, label) = PinIcon.info(shop.pin);
          final grades = d['grades'] as List, viols = d['violation_details'] as List;
          final text = Theme.of(context).textTheme;
          return ListView(padding: const EdgeInsets.all(16), children: [
            Row(children: [
              SizedBox(width: 56, height: 56, child: PinIcon(shop.pin)),
              const SizedBox(width: 12),
              Expanded(child: Text(shop.name, style: text.headlineSmall)),
            ]),
            const SizedBox(height: 8),
            Text(label, style: text.titleMedium),
            Text(shop.addr),
            const Divider(height: 32),
            Text('위생등급', style: text.titleMedium),
            if (grades.isEmpty)
              const Text('지정 정보 없음 (위생등급은 가게가 자율로 신청하는 제도입니다)')
            else
              for (final g in grades) Text('${g['level']} · ${g['asgn_from']} ~ ${g['asgn_to']} · ${g['agency']}'),
            const Divider(height: 32),
            Text('행정처분', style: text.titleMedium),
            if (viols.isEmpty)
              const Text('현재 공표 중인 위생 처분 없음')
            else
              for (final v in viols)
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text('[${_category[v['category']] ?? '기타'}] ${v['dsps_type']}'),
                  subtitle: Text('${v['content']}\n처분일 ${v['decided']} · 공표 ~${v['public_until']}'),
                ),
            const SizedBox(height: 24),
            Text('출처: 식품의약품안전처 식품안전나라. 공표 기간이 지난 처분은 표시하지 않습니다.', style: text.bodySmall),
          ]);
        },
      ),
    );
  }
}
