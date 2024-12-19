package app.nyangweso.kafkacustomersconsumer.mappers;

import ...

public interface CustomersMapper {

    default Instant map(Timestamp timestamp){
        return Instant.ofEpochSecond( timestamp.getSeconds() , timestamp.getNanos() ) ;
    }
}