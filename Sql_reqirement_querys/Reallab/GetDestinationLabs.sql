-- Drop the procedure if it already exists
IF OBJECT_ID('dbo.GetDestinationLabs', 'P') IS NOT NULL
    DROP PROCEDURE dbo.GetDestinationLabs;
GO

-- Create the stored procedure to fetch destination labs
CREATE PROCEDURE dbo.GetDestinationLabs
AS
BEGIN
    SET NOCOUNT ON;
    SELECT [gehahid], [gehahname]
    FROM [Patients].[dbo].[Gehats]
    WHERE morsel != 0;
END
GO