from pyteal import *


class Car:
    class Variables:
        brand = Bytes("NAME")
        image = Bytes("IMAGE")
        description = Bytes("DESCRIPTION")
        location = Bytes("LOCATION")
        price = Bytes("PRICE")
        available = Bytes("AVAILABLE")
        sold = Bytes("Sold")
       
        

    class AppMethods:
        buy = Bytes("buy")
        addmorecars = Bytes("addmorecars")
        changelocation = Bytes("changelocation")
       

    #new car listing
    def application_creation(self):
        return Seq([
            Assert(
                And(
                    Txn.application_args.length() == Int(5),
                    Txn.note() == Bytes("rider:uv1"),
                    Len(Txn.application_args[0]) > Int(0),
                    Len(Txn.application_args[1]) > Int(0),
                    Len(Txn.application_args[2]) > Int(0),
                     Len(Txn.application_args[3]) > Int(0),
                    Btoi(Txn.application_args[4]) > Int(0),
                    Len(Txn.application_args[5]) > Int(0),
                )
            ), 

          
            App.globalPut(self.Variables.brand, Txn.application_args[0]),
            App.globalPut(self.Variables.image, Txn.application_args[1]),
            App.globalPut(self.Variables.description, Txn.application_args[2]),
             App.globalPut(self.Variables.location, Txn.application_args[3]),
            App.globalPut(self.Variables.price, Btoi(Txn.application_args[4])),
            App.globalPut(self.Variables.available, Txn.application_args[5]),
            App.globalPut(self.Variables.sold, Int(0)),

            Approve(),
        ])

  #buy car
    def buy(self):
            count = Txn.application_args[1]
            valid_number_of_transactions = Global.group_size() == Int(2)

            valid_payment_to_seller = And(
                Gtxn[1].type_enum() == TxnType.Payment,
                Gtxn[1].receiver() == Global.creator_address(),
                Gtxn[1].amount() == App.globalGet(self.Variables.price),
                Gtxn[1].sender() == Gtxn[0].sender(),
            )

            can_buy = And(valid_number_of_transactions,
                        valid_payment_to_seller)

            update_state = Seq([
                App.globalPut(self.Variables.sold, App.globalGet(self.Variables.sold) + Int(1)),
                App.globalPut(self.Variables.available, App.globalGet(self.Variables.available) - Int(1)),
                Approve()
            ])

            return If(can_buy).Then(update_state).Else(Reject())

    
  # add more car to the listing
    def addmorecars(self):
        Assert(
            And(
                    Txn.sender() == Global.creator_address(),
                    Txn.applications.length() == Int(1),
                    Txn.application_args.length() == Int(2),
            ),
        ),
        return Seq([
            App.globalPut(self.Variables.available, Txn.application_args[2]),
            Approve()
        ])


    #change location
    def changelocation(self):
        Assert(
            And(
                    Txn.sender() == Global.creator_address(),
                    Txn.applications.length() == Int(1),
                    Txn.application_args.length() == Int(2),
            ),
        ),
        return Seq([
            App.globalPut(self.Variables.location, Txn.application_args[2]),
            Approve()
        ])


    #delete car
    def application_deletion(self):
        return Return(Txn.sender() == Global.creator_address())

   
    def application_start(self):
        return Cond(
            # checks if the application_id field of a transaction matches 0.
            # If this is the case, the application does not exist yet, and the application_creation() method is called
            [Txn.application_id() == Int(0), self.application_creation()],
            # If the the OnComplete action of the transaction is DeleteApplication, the application_deletion() method is called
            [Txn.on_completion() == OnComplete.DeleteApplication,
             self.application_deletion()],
            [Txn.application_args[0] == self.AppMethods.buy, self.buy()],
            [Txn.application_args[0] == self.AppMethods.addmorecars, self.addmorecars()],
            [Txn.application_args[0] == self.AppMethods.changelocation, self.changelocation()],
        )

    # The approval program is responsible for processing all application calls to the contract.
    def approval_program(self):
        return self.application_start()

    # The clear program is used to handle accounts using the clear call to remove the smart contract from their balance record.
    def clear_program(self):
        return Return(Int(1))