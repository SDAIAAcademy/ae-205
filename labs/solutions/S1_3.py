"""Solution of lab 1.3: schemas from the contract, problem details for every error, a versioned path."""

from common import check, expect_fail, fresh, restore, say, sh

lab = fresh("1.3")
code, out = sh(["uv", "run", "--quiet", "pytest", "tests/test_contract.py"], lab, check=False)
print(out.splitlines()[-1])
assert code != 0
expect_fail("1.3")
say("the finished schemas, error handlers and route")
restore(lab, "src/rifd/schemas.py", "src/rifd/errors.py", "src/rifd/app.py")
out = sh(["uv", "run", "--quiet", "pytest", "tests/test_contract.py"], lab)[1]
print(out.splitlines()[-1])
check("1.3")
