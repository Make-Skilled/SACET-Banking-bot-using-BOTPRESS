App = {
  
    web3Provider: null,
    contracts: {},
      
    init: async () => {
    
     
        await App.initWeb3();
        await App.initContract();
        await App.checkLogin();
      
    },
  
    initWeb3:  async () => {
  
      if(window.web3) {
        App.web3Provider = window.web3.currentProvider;
        console.log('Metamask Available');
      }
      else {
        App.web3Provider = new Web3.providers.HttpProvider('http://localhost:8545');
        console.log('Ganache Available');
      }
  
      web3 = new Web3(App.web3Provider);
      return App.initContract();
    },
  
    initContract:  async () => {
  
      $.getJSON('Bank.json',function(data){
  
        var bankArtifact = data;
        App.contracts.bank = TruffleContract(bankArtifact);
        App.contracts.bank.setProvider(App.web3Provider);
      });
        return App.checkLogin();
    },
  
    checkLogin:  async () => {
  
        value = parseInt(localStorage.login);
        console.log(value);
  
        if(value == 0)
        {
          alert('You are not logged in !!')
          window.location.href = "login.html"
        }
        
      return App.bindEvents();
    },
  
    bindEvents: function() {
  
      $(document).on('click', '.btn-checkBalance', App.getBalance);
    },  
  
    getBalance:function(event) {
  
      const u = localStorage.account;
      const user = parseInt(u);
      console.log(user);
  
      var bankInstance;
  
      web3.eth.getAccounts(function(error,accounts){
  
        if(error) {
          console.log(error);
        }
  
        var account=accounts[0];
        console.log(account);
  
        App.contracts.bank.deployed().then(function(instance){
          
          bankInstance=instance;
          return bankInstance.getBalance(user,{from:account});
  
        }).then(function(result){
  
          const balance=(result.toNumber());
          $('#bal').html(balance);
  
          var delayInMilliseconds = 3000; 
  
          setTimeout(function() {
            $('#bal').html('*****');
           }, delayInMilliseconds);
  
        }).catch(function(err){
          console.log(err.message);
        });
  
      });
    }
   
  }
  
  $(function() {
    $(window).load(function() {
      App.init();
    });
  });