package app.nyangweso.kafkacustomersconsumer.dtos;

import ...
/**
 * @author Rodgers
 * <p>
 * Date: 25/10/2024
 * Time: 11:05 AM
 * <p>
 */
public class CustomersDto {
    @JsonProperty("id")
    private String id;
    @JsonProperty("first_name")
    private String firstName;
    @JsonProperty("last_name")
    private String lastName;
    @JsonProperty("created_by")
    private String createdBy;
    @JsonProperty("updated_by")
    private String updatedBy;
}