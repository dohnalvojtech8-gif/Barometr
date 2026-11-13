"""User-measured, monotone per-product/per-capacity height-to-volume profiles.

Interpolation improves the mapping for irregular bottles. It does not validate
measurements or establish the accuracy of optical coordinates.
"""
import math


class CalibrationError(ValueError):
    pass


def validate_points(points, capacity):
    if not isinstance(points,list) or not 5 <= len(points) <= 30:
        raise CalibrationError('Zadejte nejméně 5 bodů včetně prázdné a plné lahve, nejvýše 30.')
    clean=[]
    for point in points:
        if not isinstance(point,dict):raise CalibrationError('Neplatný kalibrační bod.')
        fraction,ml=point.get('fraction'),point.get('ml')
        if any(type(v) not in (int,float) or not math.isfinite(v) for v in (fraction,ml)):
            raise CalibrationError('Kalibrační body musí být konečná čísla.')
        if not 0<=fraction<=1 or not 0<=ml<=capacity:raise CalibrationError('Bod je mimo rozsah lahve.')
        clean.append({'fraction':float(fraction),'ml':float(ml)})
    clean.sort(key=lambda p:p['fraction'])
    if clean[0]!={'fraction':0.,'ml':0.} or clean[-1]!={'fraction':1.,'ml':float(capacity)}:
        raise CalibrationError('První bod musí být 0 % / 0 ml a poslední 100 % / plná kapacita.')
    for a,b in zip(clean,clean[1:]):
        if b['fraction']-a['fraction']<.01 or b['ml']<=a['ml']:
            raise CalibrationError('Výška i objem musí přísně růst. Body oddělte alespoň o 1 % výšky.')
    return clean


def interpolate(fraction,points,capacity):
    points=validate_points(points,capacity)
    if type(fraction) not in (int,float) or not math.isfinite(fraction) or not 0<=fraction<=1:
        raise CalibrationError('Výška hladiny je mimo kalibrovaný rozsah.')
    for a,b in zip(points,points[1:]):
        if fraction<=b['fraction']:
            return a['ml']+(fraction-a['fraction'])/(b['fraction']-a['fraction'])*(b['ml']-a['ml'])
    return float(capacity)
