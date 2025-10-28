/** Custom exceptions for CortexDB SDK */

/**
 * Base exception for all CortexDB errors
 */
export class CortexDBError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CortexDBError";
    Object.setPrototypeOf(this, CortexDBError.prototype);
  }
}

/**
 * Exception raised for connection errors
 */
export class CortexDBConnectionError extends CortexDBError {
  constructor(message: string = "Failed to connect to CortexDB") {
    super(message);
    this.name = "CortexDBConnectionError";
    Object.setPrototypeOf(this, CortexDBConnectionError.prototype);
  }
}

/**
 * Exception raised for timeout errors
 */
export class CortexDBTimeoutError extends CortexDBError {
  constructor(message: string = "Request timed out") {
    super(message);
    this.name = "CortexDBTimeoutError";
    Object.setPrototypeOf(this, CortexDBTimeoutError.prototype);
  }
}

/**
 * Exception raised for 404 Not Found errors
 */
export class CortexDBNotFoundError extends CortexDBError {
  constructor(message: string = "Resource not found") {
    super(message);
    this.name = "CortexDBNotFoundError";
    Object.setPrototypeOf(this, CortexDBNotFoundError.prototype);
  }
}

/**
 * Exception raised for validation errors (400)
 */
export class CortexDBValidationError extends CortexDBError {
  constructor(message: string = "Validation error") {
    super(message);
    this.name = "CortexDBValidationError";
    Object.setPrototypeOf(this, CortexDBValidationError.prototype);
  }
}

/**
 * Exception raised for authentication errors (401)
 */
export class CortexDBAuthenticationError extends CortexDBError {
  constructor(message: string = "Authentication failed") {
    super(message);
    this.name = "CortexDBAuthenticationError";
    Object.setPrototypeOf(this, CortexDBAuthenticationError.prototype);
  }
}

/**
 * Exception raised for permission errors (403)
 */
export class CortexDBPermissionError extends CortexDBError {
  constructor(message: string = "Permission denied") {
    super(message);
    this.name = "CortexDBPermissionError";
    Object.setPrototypeOf(this, CortexDBPermissionError.prototype);
  }
}

/**
 * Exception raised for server errors (5xx)
 */
export class CortexDBServerError extends CortexDBError {
  constructor(message: string = "Server error") {
    super(message);
    this.name = "CortexDBServerError";
    Object.setPrototypeOf(this, CortexDBServerError.prototype);
  }
}

