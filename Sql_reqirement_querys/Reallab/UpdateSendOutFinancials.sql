-- Drop the procedure if it already exists
IF OBJECT_ID('dbo.UpdateSendOutFinancials', 'P') IS NOT NULL
    DROP PROCEDURE dbo.UpdateSendOutFinancials;
GO

-- Create the stored procedure to update financials and log payment
CREATE PROCEDURE dbo.UpdateSendOutFinancials
    @PatientID NVARCHAR(50),
    @TestName NVARCHAR(100),
    @Price REAL,
    @AmountPaid REAL,
    @DestinationLab NVARCHAR(50),
    @EditDate NVARCHAR(40),
    @Status NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    BEGIN TRY
        BEGIN TRANSACTION;

        -- Update patienttest with new Price, Amount Paid, and Destination Lab
        UPDATE dbo.patienttest
        SET testpriceout = @Price,
            testpriceoutmadfo = @AmountPaid,
            otherlabname = @DestinationLab
        WHERE patientid = @PatientID AND testsimp = @TestName;

        -- Handle Status Change
        IF @Status = 'Pending'
        BEGIN
            -- Remove from SendOutLog to revert status to Pending
            DELETE FROM dbo.SendOutLog WHERE PatientID = @PatientID AND TestName = @TestName;
        END
        ELSE IF @Status = 'Sent'
        BEGIN
            -- Ensure it exists in SendOutLog
            IF NOT EXISTS (SELECT 1 FROM dbo.SendOutLog WHERE PatientID = @PatientID AND TestName = @TestName)
            BEGIN
                INSERT INTO dbo.SendOutLog (PatientID, TestName, SentDate) VALUES (@PatientID, @TestName, GETDATE());
            END
        END

        -- Check if payment exists to prevent duplicates
        IF EXISTS (SELECT 1 FROM dbo.payment WHERE patientid = @PatientID AND testsimp = @TestName)
        BEGIN
            UPDATE dbo.payment
            SET money = @AmountPaid,
                gehah = @DestinationLab,
                editdate = @EditDate
            WHERE patientid = @PatientID AND testsimp = @TestName;
        END
        ELSE
        BEGIN
            -- Insert into payment table
            INSERT INTO dbo.payment (
                patientid, paiddate, type, gehah, testsimp, money, mowzaf, editdate, comment
            )
            VALUES (
                @PatientID, GETDATE(), 3, @DestinationLab, @TestName, @AmountPaid, 'Admin', @EditDate, NULL
            );
        END

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END
GO