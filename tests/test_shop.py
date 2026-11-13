import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from server.shop import build_templates,choose_week,quote,week_window,cents,ELITE_IDS

CATALOG=json.loads((Path(__file__).parents[1]/'aplikace/catalog-data.js').read_text().split(' = ',1)[1].rstrip(';\n'))
PRODUCTS={p['id']:p for p in CATALOG['products']}
TEMPLATES=build_templates(list(PRODUCTS.values()))


def test_price_range_and_curated_elite():
 assert min(cents(p) for p in PRODUCTS.values())==39
 assert {p['id'] for p in PRODUCTS.values() if cents(p)==99}==ELITE_IDS
 assert all(39<=cents(p)<=99 for p in PRODUCTS.values())


def test_large_persistable_unique_themed_pool_and_real_savings():
 assert len(TEMPLATES)>1000
 assert len({t['id'] for t in TEMPLATES})==len(TEMPLATES)
 assert len({tuple(t['productIds']) for t in TEMPLATES})==len(TEMPLATES)
 categories={p['category'] for p in PRODUCTS.values()}
 for t in TEMPLATES:
  assert len(t['productIds'])>=2 and len(set(t['productIds']))==len(t['productIds'])
  members=[PRODUCTS[id] for id in t['productIds']]
  if t['theme'] in categories:assert all(p['category']==t['theme'] for p in members)
  else:assert all(p['name'].casefold().startswith(t['theme'].casefold()) for p in members)
  q=quote(t,PRODUCTS)
  assert 39<=q['priceCents']<q['regularCents']
  assert q['savingCents']==q['regularCents']-q['priceCents']
  if t['kind']=='collection':assert q['savingCents'] in (200,300,400,500)
  assert quote(t,PRODUCTS,t['productIds'])['personalPriceCents']==0
  partial=quote(t,PRODUCTS,t['productIds'][:-1]);assert 0<partial['personalPriceCents']<=partial['remainingRegularCents']


def test_requested_jager_deal_all_sizes_and_weekly_rotation():
 tz=ZoneInfo('Europe/Prague');first=choose_week(TEMPLATES,datetime(2026,11,13,12,tzinfo=tz));second=choose_week(TEMPLATES,datetime(2026,11,16,0,tzinfo=tz))
 assert len(first['offers'])==8 and len(second['offers'])==8
 assert not {t['id'] for t in first['offers']} & {t['id'] for t in second['offers']}
 jager=next(t for t in first['offers'] if t['special'])
 assert jager['priceCents']==49
 assert set(jager['productIds'])=={'jagermeister','p-33f095ed39ac','p-46579803807e'}
 assert quote(jager,PRODUCTS)['products'][0]['variants']
 assert week_window(datetime(2027,1,1,tzinfo=tz))[:2]==('2026-12-28','2027-01-04')
 dst=choose_week(TEMPLATES,datetime(2027,3,22,tzinfo=tz));assert dst['expiresAt'].endswith('+02:00')
 # Last moment of a week and first moment of the next choose different offers.
 assert choose_week(TEMPLATES,datetime(2026,11,15,23,59,59,tzinfo=tz))['weekKey']=='2026-11-09'
 assert second['weekKey']=='2026-11-16'
