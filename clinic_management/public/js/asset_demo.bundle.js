import { sayHello } from './asset_demo_1.js';
import { calculate } from './asset_demo_2.js';

console.log(sayHello());
console.log("Result:", calculate(10, 20));

frappe.require("asset_demo.bundle.js").then(() => {
    console.log("Asset bundle loaded successfully!");
});