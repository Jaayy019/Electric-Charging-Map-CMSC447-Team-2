function SignUp({ onLoginSuccess, goToLogin }) {
  const body = {
    backgroundColor: '#0080ff', 
    fontFamily: "'Open Sans', sans-serif",
    display: 'flex',
    justifyContent: 'center',
    width: '100vw',
    height: '100vh',
    padding: '1rem'
  };

  const formBody = {
    width: '50vw',
    height: '40vh',
    padding: '1rem',
    backgroundColor: 'white'
  };

  return (
    <>
      <title>Sign Up</title>
      <div class="container" style={body}>
        <form class="loginForm" style={formBody}>

          <h1 style={{ textAlign: 'center' }}>Create an account</h1>
          <br/>

          <div class="input-group">
            <label for="username" class="label">Username: </label>
            <input type="text" id="username" class="input"></input>
            <span class="error-message"></span>
          </div>

          <div class="input-group">
            <label for="password" class="label">Password: </label>
            <input type="password" id="password" class="password"></input>
            <span class="error-message"></span>
          </div>

          <br/>
          <button onClick={ onLoginSuccess }>Login</button>
          <button onClick={ goToLogin }>Already have an account? Login</button>

        </form>
      </div>
    </>
  );
}
export default SignUp;