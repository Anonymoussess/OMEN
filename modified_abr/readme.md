# What we did 

Using CC statistics data to improve ABR algorithm in DASH.js

[//]: # ( todo)


## How to use

1. Download dash.js (We are using version 4.7.3, but due to the weak correlation between our code and the original ABR algorithm, its only need one function call and passing switchRequest and ruleContext as args. So it should also be applied to new versions with less significant changes)
2. Copy the code of [addition_part.js](addition_part.js) from this directory to the corresponding ABR algorithm in the ` src/streaming/abr/rules/` directory of dash.js (for specific methods, please refer to [ThroughputRule.js](ThroughputRule.js) and [BolaRule. js](BolaRule.js)). In this way, our policy can be called in the ABR algorithm.
3. If you use the exact same method as the two reference files mentioned above to access, you will observe the debugging output in the console of the dash player page (the explanation of the output can be found in the supporting materials section of the paper)
4. Compile it, and the subsequent use will be the same as the original dash.js


## Additional Notes

We have provided our compiled dist folder, as well as the original dash compilation results corresponding to the version, which can be directly overwritten for use.

