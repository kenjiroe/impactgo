.PHONY: run serve admin test clean
run:    ; ./run.sh
serve:  ; ./serve.sh
admin:  ; ./admin.sh
test:   ; python3 tests/test_normalize.py && python3 tests/test_parse.py && python3 tests/test_ttm.py
clean:  ; rm -rf site/ics site/index.html site/data.json
