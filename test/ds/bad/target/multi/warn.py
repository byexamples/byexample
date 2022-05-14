from byexample.finder import ZoneDelimiter

stability = 'provisional'

class MultiTargetDuplicated(ZoneDelimiter):
   # This is not an error but clearly a typo.
   target = ['foo', 'foo']

class MultiTargetEmpty(ZoneDelimiter):
   # This is not an error but setting to None is better
   # to make explicit the intention
   target = []
