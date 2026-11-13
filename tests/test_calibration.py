import pytest
from server.calibration import validate_points,interpolate,CalibrationError
from server.vision import validate_result,VisionError

POINTS=[{'fraction':0,'ml':0},{'fraction':.25,'ml':70},{'fraction':.5,'ml':200},{'fraction':.75,'ml':420},{'fraction':1,'ml':700}]

def test_non_linear_measured_profile_interpolation():
 assert interpolate(.5,POINTS,700)==200 # Linear height model would incorrectly return 350 ml.
 assert interpolate(.375,POINTS,700)==135
 assert interpolate(0,POINTS,700)==0 and interpolate(1,POINTS,700)==700
 for bad in (POINTS[:4],[{**p,'ml':-1} for p in POINTS],POINTS+POINTS[:1],[{**p,'fraction':float('nan')} for p in POINTS]):
  with pytest.raises(CalibrationError):validate_points(bad,700)
 with pytest.raises(CalibrationError):interpolate(1.1,POINTS,700)
 with pytest.raises(CalibrationError):validate_points(POINTS,1000)


def test_vision_uses_measured_profile_for_irregular_shape_and_checks_reference_drift():
 frame={'bottle_count':1,'matches_product':True,'level_visible':True,'bottle_fully_visible':True,'constant_section':False,'full_y':.2,'level_y':.5,'bottom_y':.8}
 result={'frames':[frame.copy(),frame.copy()]}
 assert validate_result(result,700)['detected'] is False
 profile={'capacity':700,'points':POINTS,'updatedAt':123}
 value=validate_result(result,700,profile)
 assert value['detected'] is True and value['ml']==200 and value['calibrated'] is True
 assert value['accuracyVerified'] is False and value['calibrationUpdatedAt']==123
 with pytest.raises(VisionError):validate_result(result,700,{**profile,'capacity':1000})
 result['frames'][1]['full_y']=.3
 assert validate_result(result,700,profile)['detected'] is False
