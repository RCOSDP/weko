# radon



## install


## run

```
radon cc -i "docs,tests,examples" -s . > test/radon/cc_result.txt
radon cc -o SCORE -n B -x F -s -i "tests,examples,docs" modules/ > test/radon/cc_result2.txt
radon mi -i "docs,tests,examples" -s . > test/radon/mi_result.txt
radon raw -i "docs,tests,examples" -s . > test/radon/raw_result.txt
```
