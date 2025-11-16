
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='SendOutLog' and xtype='U')
BEGIN
    CREATE TABLE dbo.SendOutLog (
        LogID INT PRIMARY KEY IDENTITY(1,1),
        PatientID NVARCHAR(50) NOT NULL,
        TestName NVARCHAR(100) NOT NULL,
        SentDate DATETIME NOT NULL,
        CONSTRAINT UQ_SendOutLog UNIQUE (PatientID, TestName, SentDate)
    );
END
