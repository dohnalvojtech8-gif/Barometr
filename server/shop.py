"""Deterministic weekly offers; all arithmetic uses integer euro cents."""
import hashlib
import math
import re
from collections import defaultdict
from datetime import datetime, date, timedelta, time
from zoneinfo import ZoneInfo

EPOCH = date(2026, 11, 9)
ELITE_IDS = {'p-1c0764c73d15', 'p-771ecab15dfb', 'p-effb3281a332'}


def cents(product):
    return round(product['unlockPrice'] * 100)


def week_window(now=None):
    now = now or datetime.now(ZoneInfo('Europe/Prague'))
    local = now.astimezone(ZoneInfo('Europe/Prague'))
    monday = local.date() - timedelta(days=local.weekday())
    return monday.isoformat(), (monday + timedelta(days=7)).isoformat(), (monday - EPOCH).days // 7


def build_templates(products):
    templates, seen = [], set()
    def add(title, theme, members, fixed=None, special=False):
        ids = sorted({p['id'] for p in members})
        if len(ids) < 2 or tuple(ids) in seen:
            return
        seen.add(tuple(ids))
        regular = sum(cents(p) for p in members if p['id'] in ids)
        if fixed is None and len(ids) >= 8:
            discount = next((saving for size, saving in ((24, 500), (18, 400), (12, 300), (8, 200))
                             if len(ids) >= size and regular - saving >= 39), None)
            if discount is None:
                return
            price = regular - discount
        elif fixed is None:
            price = max(39, math.ceil(regular * .65 / 10) * 10 - 1)
        else:
            price = fixed
        if price >= regular or price < 39:
            return
        identifier = 'pack-' + hashlib.sha256('|'.join(ids).encode()).hexdigest()[:16]
        templates.append({'id': identifier, 'title': title, 'theme': theme, 'productIds': ids,
                          'priceCents': price, 'special': special,
                          'kind': 'collection' if len(ids) >= 8 else 'duo'})
    jager = [p for p in products if p['id'] == 'jagermeister' or p['name'] == 'Jägermeister ORANGE']
    add('Jägermeister + Orange — všechny objemy', 'Jägermeister', jager, fixed=49, special=True)
    brands = defaultdict(list)
    categories = defaultdict(list)
    # Brand labels are kept conservative: only an explicit shared name prefix.
    compound = ('Captain Morgan', 'Johnnie Walker', 'Jack Daniel', 'Jim Beam', 'Jose Cuervo',
                'Don Julio', 'Sierra', 'Absolut', 'Bacardi', 'Božkov', 'Beefeater', 'Bombay',
                'Havana Club', 'Jägermeister', 'Jameson', 'Chivas Regal', 'Glenfiddich',
                'Remy Martin', 'Hennessy', 'Zacapa', 'Plantation', 'Planteray', 'Diplomatico',
                'Diplomático', 'Legendario', 'El Dorado', 'St. Nicolaus', 'Fernet Stock')
    for p in products:
        name = p['name']
        brand = next((b for b in compound if name.casefold().startswith(b.casefold())), name.split()[0])
        if len(brand) >= 3 and brand.casefold() not in {'rum','ron','gin','vodka','old','new','the','royal','saint','san','svatý'}:
            brands[brand].append(p)
        categories[p['category']].append(p)
    for brand, members in sorted(brands.items()):
        members = sorted(members, key=lambda p: (p['name'].casefold(), p['id']))
        if len(members) <= 30:
            add(brand + ' — kolekce', brand, members)
        for size in (2, 4, 8, 12, 18, 24):
            for start in range(0, len(members) - size + 1, max(1, size // 2)):
                group = members[start:start + size]
                add(f'{brand} — výběr {start + 1}–{start + size}', brand, group)
    for category, members in sorted(categories.items()):
        # Many genuinely themed sets, not randomly mixed brands/categories.
        members = sorted(members, key=lambda p: hashlib.sha256((category + ':' + p['id']).encode()).hexdigest())
        for size in (8, 12, 18, 24):
            for start in range(0, len(members) - size + 1, max(4, size // 2)):
                add(f'{category} — barová kolekce {start + 1}–{start + size}', category, members[start:start + size])
    return templates


def choose_week(templates, now=None):
    start, end, index = week_window(now)
    small = sorted((t for t in templates if t['kind'] == 'duo'),
                   key=lambda t: (not t.get('special'), hashlib.sha256(t['id'].encode()).hexdigest()))
    large = sorted((t for t in templates if t['kind'] == 'collection'), key=lambda t: t['id'])
    def pick(pool, slots):
        if not pool:
            return []
        return [pool[(index * slots + i) % len(pool)] for i in range(min(slots, len(pool)))]
    return {'weekKey': start, 'validUntil': end, 'timezone': 'Europe/Prague',
            'expiresAt': datetime.combine(date.fromisoformat(end),time.min,tzinfo=ZoneInfo('Europe/Prague')).isoformat(),
            'serverNow': (now or datetime.now(ZoneInfo('Europe/Prague'))).isoformat(),
            'offers': pick(small, 2) + pick(large, 6)}


def quote(template, products, owned=()):
    members = [products[id] for id in template['productIds'] if id in products]
    regular = sum(cents(p) for p in members)
    price = min(template['priceCents'], regular)
    remaining = [p for p in members if p['id'] not in owned]
    remaining_regular = sum(cents(p) for p in remaining)
    personal = min(remaining_regular, max(39, math.ceil(price * remaining_regular / regular))) if remaining_regular else 0
    return {**template, 'regularCents': regular, 'priceCents': price,
            'savingCents': regular - price, 'remainingRegularCents': remaining_regular,
            'personalPriceCents': personal, 'remainingCount': len(remaining),
            'ownedCount': len(members) - len(remaining), 'currency': 'EUR',
            'products': [{'id': p['id'], 'name': p['name'], 'abv':p['abv'], 'variants': [v['ml'] for v in p['variants']],
                          'owned': p['id'] in owned} for p in members]}
