test('ordinary Debug viewing does not request a collector; explicit opt-in still works', () => {
  jest.isolateModules(() => {
    const fetchSpy = jest.spyOn(global, 'fetch').mockResolvedValue({ ok: true } as Response);
    const { beacon, setBeaconEnabled } = require('../../src/calmframes/timingLog');
    try {
      beacon('ordinary-viewing');
      expect(fetchSpy).not.toHaveBeenCalled();
      setBeaconEnabled(true);
      beacon('measurement');
      expect(fetchSpy).toHaveBeenCalledTimes(1);
      setBeaconEnabled(false);
      beacon('ordinary-viewing-again');
      expect(fetchSpy).toHaveBeenCalledTimes(1);
    } finally { fetchSpy.mockRestore(); }
  });
});
