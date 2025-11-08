// Refactoring Test - Code that needs improvement
// A coding agent should be able to identify and fix code smells

// Bad practice: Global variables
var globalCounter = 0;
var globalData = [];

// Bad practice: Long function with multiple responsibilities
function processUserData(name, age, email, address, phone) {
    // Validation
    if (!name || name.length === 0) {
        console.log("Name is required");
        return false;
    }
    if (!email || email.indexOf("@") === -1) {
        console.log("Invalid email");
        return false;
    }
    if (age < 0 || age > 150) {
        console.log("Invalid age");
        return false;
    }

    // Data processing
    var user = {
        name: name,
        age: age,
        email: email,
        address: address,
        phone: phone,
        id: globalCounter++
    };

    // Data storage
    globalData.push(user);

    // Logging
    console.log("User added: " + name);
    console.log("Total users: " + globalData.length);

    return true;
}

// Bad practice: Duplicated code
function findUserByEmail(email) {
    for (var i = 0; i < globalData.length; i++) {
        if (globalData[i].email === email) {
            return globalData[i];
        }
    }
    return null;
}

function findUserByName(name) {
    for (var i = 0; i < globalData.length; i++) {
        if (globalData[i].name === name) {
            return globalData[i];
        }
    }
    return null;
}

// Bad practice: Magic numbers
function calculateDiscount(price, userAge) {
    if (userAge < 18) {
        return price * 0.9;
    } else if (userAge > 65) {
        return price * 0.85;
    }
    return price;
}

// Test the functions
processUserData("John Doe", 30, "john@example.com", "123 Main St", "555-1234");
processUserData("Jane Smith", 25, "jane@example.com", "456 Oak Ave", "555-5678");

console.log(findUserByEmail("john@example.com"));
console.log(calculateDiscount(100, 70));
